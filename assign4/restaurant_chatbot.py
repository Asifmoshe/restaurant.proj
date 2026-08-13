"""Restaurant chatbot logic for Assignment 4.

This file does the main chatbot work:
1. Understands the user's intent
2. Books reservations
3. Cancels reservations
4. Answers menu and opening-hours questions
5. Sends reservation/cancellation events to n8n using a webhook
"""

import os
import re
from typing import Any, Dict, Optional
import requests

from restaurant_db import (
    book_reservation,
    cancel_reservation,
    get_menu_items,
    get_reservations,
    get_restaurant_details_and_hours,
    initialize_database,
    search_menu_items,
)


DB_PATH = "restaurant.sqlite"

# Later, n8n will listen on this URL.
# For now, if n8n is not running, the chatbot will still work.
N8N_WEBHOOK_URL = os.getenv(
    "N8N_WEBHOOK_URL",
    "http://localhost:5678/webhook/restaurant",
)


def classify_intent(user_message: str) -> str:
    """Classify the user message into one of the assignment categories."""

    message = user_message.lower()

    # Important: cancellation should be checked before reservation.
    if any(word in message for word in ["cancel", "delete booking", "remove reservation"]):
        return "cancellation"

    if any(word in message for word in ["reserve", "reservation", "book", "table"]):
        return "reservation"

    if any(word in message for word in ["menu", "food", "dish", "pizza", "burger", "dessert", "drink"]):
        return "menu"

    if any(word in message for word in ["open", "close", "hours", "time", "address", "phone"]):
        return "hours"

    return "general"


def extract_email_or_phone(user_message: str) -> str:
    """Extract an email or phone number from the user message if possible."""

    email_match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        user_message,
    )

    if email_match:
        return email_match.group(0)

    phone_match = re.search(
        r"\b(?:\+972[- ]?)?(?:0)?(?:5\d|[23489])[- ]?\d{3}[- ]?\d{4}\b",
        user_message,
    )

    if phone_match:
        return phone_match.group(0)

    return ""


def extract_name(user_message: str) -> Optional[str]:
    """Extract customer name from simple phrases."""

    patterns = [
        r"my name is ([A-Za-z ]+)",
        r"name is ([A-Za-z ]+)",
        r"under ([A-Za-z ]+)",
        r"for ([A-Za-z ]+) on \d{4}-\d{2}-\d{2}",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)

        if match:
            name = match.group(1).strip()

            # Clean extra words if the name capture is too long.
            name = re.split(
                r"\bfor\b|\bat\b|\bon\b|\bwith\b|\bcontact\b",
                name,
                flags=re.IGNORECASE,
            )[0].strip()

            if name:
                return name.title()

    return None


def extract_party_size(user_message: str) -> Optional[int]:
    """Extract number of people for the reservation."""

    patterns = [
        r"for (\d+) people",
        r"for (\d+) guests",
        r"for (\d+) persons",
        r"table for (\d+)",
        r"party of (\d+)",
        r"for (\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def extract_date(user_message: str) -> Optional[str]:
    """Extract date in YYYY-MM-DD format."""

    date_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", user_message)

    if date_match:
        return date_match.group(0)

    return None


def extract_time(user_message: str) -> Optional[str]:
    """Extract time as HH:MM or convert simple 8pm / 8:30pm format."""

    # Format like 19:30
    time_24h_match = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", user_message)

    if time_24h_match:
        hour = int(time_24h_match.group(1))
        minute = int(time_24h_match.group(2))
        return f"{hour:02d}:{minute:02d}"

    # Format like 8pm or 8:30pm
    time_pm_am_match = re.search(
        r"\b(\d{1,2})(?::([0-5]\d))?\s*(am|pm)\b",
        user_message,
        re.IGNORECASE,
    )

    if time_pm_am_match:
        hour = int(time_pm_am_match.group(1))
        minute = int(time_pm_am_match.group(2) or 0)
        am_pm = time_pm_am_match.group(3).lower()

        if am_pm == "pm" and hour != 12:
            hour += 12

        if am_pm == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}"

    return None


def extract_reservation_details(user_message: str) -> Dict[str, Any]:
    """Extract reservation details from the user message."""

    return {
        "customer_name": extract_name(user_message),
        "reservation_date": extract_date(user_message),
        "reservation_time": extract_time(user_message),
        "party_size": extract_party_size(user_message),
        "contact": extract_email_or_phone(user_message),
    }


def extract_reservation_id(user_message: str) -> Optional[int]:
    """Extract reservation ID for cancellation."""

    patterns = [
        r"reservation id (\d+)",
        r"booking id (\d+)",
        r"reservation number (\d+)",
        r"booking number (\d+)",
        r"#(\d+)",
        r"\b(\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None


def send_n8n_webhook(event_type: str, payload: Dict[str, Any]) -> bool:
    """Send reservation/cancellation event to n8n."""

    data = {
        "event": event_type,
        **payload,
    }

    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=data,
            timeout=5,
        )

        return response.status_code < 400

    except requests.exceptions.RequestException:
        return False


def handle_reservation(user_message: str) -> str:
    """Book a reservation if all required details were provided."""

    details = extract_reservation_details(user_message)

    missing_fields = []

    if not details["customer_name"]:
        missing_fields.append("customer name")

    if not details["reservation_date"]:
        missing_fields.append("date in YYYY-MM-DD format")

    if not details["reservation_time"]:
        missing_fields.append("time, for example 19:30 or 8pm")

    if not details["party_size"]:
        missing_fields.append("party size")

    if missing_fields:
        return (
            "I can help you book a table, but I need: "
            + ", ".join(missing_fields)
            + ".\n"
            + "Example: Book a table for 4 on 2026-08-05 at 19:30. "
            + "My name is Shirel. Contact: shirel@example.com"
        )

    reservation_id = book_reservation(
        db_path=DB_PATH,
        customer_name=details["customer_name"],
        reservation_date=details["reservation_date"],
        reservation_time=details["reservation_time"],
        party_size=details["party_size"],
        contact=details["contact"],
    )

    webhook_sent = send_n8n_webhook(
        event_type="reservation",
        payload={
            "reservation_id": reservation_id,
            **details,
        },
    )

    answer = (
        f"Reservation confirmed! Your reservation ID is {reservation_id}.\n"
        f"Name: {details['customer_name']}\n"
        f"Date: {details['reservation_date']}\n"
        f"Time: {details['reservation_time']}\n"
        f"Party size: {details['party_size']}"
    )

    if webhook_sent:
        answer += "\nNotification sent to n8n."
    else:
        answer += "\nReservation was saved, but n8n notification was not sent yet."

    return answer


def handle_cancellation(user_message: str) -> str:
    """Cancel a reservation by ID."""

    reservation_id = extract_reservation_id(user_message)

    if reservation_id is None:
        return (
            "I can cancel a reservation, but I need the reservation ID.\n"
            "Example: Cancel reservation ID 1"
        )

    was_cancelled = cancel_reservation(
        db_path=DB_PATH,
        reservation_id=reservation_id,
    )

    if not was_cancelled:
        return (
            f"I could not cancel reservation ID {reservation_id}. "
            "It may not exist or it may already be cancelled."
        )

    webhook_sent = send_n8n_webhook(
        event_type="cancellation",
        payload={
            "reservation_id": reservation_id,
        },
    )

    answer = f"Reservation ID {reservation_id} was cancelled successfully."

    if webhook_sent:
        answer += "\nCancellation notification sent to n8n."
    else:
        answer += "\nCancellation was saved, but n8n notification was not sent yet."

    return answer


def handle_menu(user_message: str) -> str:
    """Answer menu questions."""

    message = user_message.lower()

    general_menu_words = [
        "menu",
        "food",
        "dishes",
        "what do you have",
        "what can i eat",
        "show me the menu",
        "full menu",
    ]

    if any(phrase in message for phrase in general_menu_words):
        items = get_menu_items(DB_PATH)
    else:
        items = search_menu_items(DB_PATH, user_message)

    if not items:
        return "I could not find matching menu items."

    answer_lines = ["Here is our menu:"]

    for item in items:
        vegetarian_text = "vegetarian" if item["is_vegetarian"] else "not vegetarian"
        spicy_text = "spicy" if item["is_spicy"] else "not spicy"

        answer_lines.append(
            f"- {item['item_name']} ({item['category']}): "
            f"{item['description']}. "
            f"Price: ${item['price']:.2f}. "
            f"{vegetarian_text}, {spicy_text}."
        )

    return "\n".join(answer_lines)


def handle_hours() -> str:
    """Answer opening hours and restaurant info questions."""

    details, hours = get_restaurant_details_and_hours(DB_PATH)

    answer_lines = [
        f"{details['name']}",
        f"Address: {details['address']}",
        f"Phone: {details['phone']}",
        "",
        "Opening hours:",
    ]

    for row in hours:
        notes = f" ({row['notes']})" if row["notes"] else ""
        answer_lines.append(
            f"- {row['day_of_week']}: {row['open_time']} - {row['close_time']}{notes}"
        )

    return "\n".join(answer_lines)


def handle_general() -> str:
    """Default answer."""

    return (
        "I can help with menu questions, opening hours, table reservations, "
        "and reservation cancellations."
    )


def process_message(user_message: str) -> str:
    """Main chatbot function."""

    initialize_database(DB_PATH)

    intent = classify_intent(user_message)

    if intent == "reservation":
        return handle_reservation(user_message)

    if intent == "cancellation":
        return handle_cancellation(user_message)

    if intent == "menu":
        return handle_menu(user_message)

    if intent == "hours":
        return handle_hours()

    return handle_general()


if __name__ == "__main__":
    initialize_database(DB_PATH)

    test_messages = [
        "What food do you have on the menu?",
        "What are your opening hours?",
        "Book a table for 4 on 2026-08-05 at 19:30. My name is Shirel. Contact: shirel@example.com",
        "Cancel reservation ID 1",
        "Show me all reservations",
    ]

    for message in test_messages:
        print("\nUSER:")
        print(message)

        print("\nBOT:")
        print(process_message(message))

        print("-" * 80)

    print("\nCurrent reservations in database:")
    for reservation in get_reservations(DB_PATH):
        print(reservation)