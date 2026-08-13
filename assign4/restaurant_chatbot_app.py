"""Terminal app for the restaurant chatbot.

Run this file to chat with the restaurant assistant in the terminal.
"""

from restaurant_chatbot import process_message


def main() -> None:
    """Start a simple terminal chat loop."""

    print("Welcome to Sunset Bistro chatbot!")
    print("You can ask about the menu, opening hours, reservations, or cancellations.")
    print("Type 'exit' to stop.")
    print("-" * 80)

    while True:
        user_message = input("\nYou: ").strip()

        if user_message.lower() in ["exit", "quit", "q"]:
            print("Bot: Goodbye!")
            break

        if not user_message:
            print("Bot: Please type a message.")
            continue

        bot_answer = process_message(user_message)

        print("\nBot:")
        print(bot_answer)


if __name__ == "__main__":
    main()