"""SQLite setup and query helpers for the restaurant chatbot assignment."""

import sqlite3
from typing import Any, Dict, List, Tuple


def initialize_database(db_path: str = "restaurant.sqlite") -> None:
    """Create restaurant tables and seed starter data."""

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS menu_items (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name       TEXT NOT NULL,
                category        TEXT NOT NULL,
                description     TEXT NOT NULL,
                price           REAL NOT NULL,
                is_vegetarian   INTEGER NOT NULL DEFAULT 0,
                is_spicy        INTEGER NOT NULL DEFAULT 0,
                is_available    INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS restaurant_details (
                id          INTEGER PRIMARY KEY CHECK (id = 1),
                name        TEXT NOT NULL,
                address     TEXT NOT NULL,
                phone       TEXT NOT NULL,
                email       TEXT NOT NULL,
                website     TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS opening_hours (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                day_of_week     TEXT NOT NULL UNIQUE,
                open_time       TEXT NOT NULL,
                close_time      TEXT NOT NULL,
                notes           TEXT
            )
            """
        )

        # New table for Assignment 4
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name       TEXT NOT NULL,
                reservation_date    TEXT NOT NULL,
                reservation_time    TEXT NOT NULL,
                party_size          INTEGER NOT NULL,
                contact             TEXT,
                status              TEXT NOT NULL DEFAULT 'booked',
                created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        _seed_if_empty(conn)


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Insert starter restaurant data only once."""

    has_menu = conn.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0] > 0
    has_details = conn.execute("SELECT COUNT(*) FROM restaurant_details").fetchone()[0] > 0
    has_hours = conn.execute("SELECT COUNT(*) FROM opening_hours").fetchone()[0] > 0

    if not has_menu:
        menu_rows = [
            ("Margherita Pizza", "Main", "Tomato, mozzarella, basil", 10.50, 1, 0, 1),
            ("Spicy Chicken Burger", "Main", "Grilled chicken, jalapeno mayo", 11.90, 0, 1, 1),
            ("Caesar Salad", "Starter", "Romaine, parmesan, croutons", 7.25, 0, 0, 1),
            ("Mushroom Risotto", "Main", "Creamy arborio rice with mushrooms", 12.75, 1, 0, 1),
            ("Lemon Tart", "Dessert", "House-made tart with lemon curd", 5.20, 1, 0, 1),
            ("Iced Latte", "Drinks", "Espresso with cold milk and ice", 4.60, 1, 0, 1),
        ]

        conn.executemany(
            """
            INSERT INTO menu_items
            (item_name, category, description, price, is_vegetarian, is_spicy, is_available)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            menu_rows,
        )

    if not has_details:
        conn.execute(
            """
            INSERT INTO restaurant_details
            (id, name, address, phone, email, website)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                "Sunset Bistro",
                "123 Dizengoff Street, Tel Aviv",
                "03-555-0142",
                "hello@sunsetbistro.example",
                "www.sunsetbistro.example",
            ),
        )

    if not has_hours:
        hours_rows = [
            ("Monday", "09:00", "21:00", ""),
            ("Tuesday", "09:00", "21:00", ""),
            ("Wednesday", "09:00", "21:00", ""),
            ("Thursday", "09:00", "22:00", ""),
            ("Friday", "09:00", "23:00", ""),
            ("Saturday", "10:00", "23:00", "Brunch menu until 14:00"),
            ("Sunday", "10:00", "20:00", "Family set menu available"),
        ]

        conn.executemany(
            """
            INSERT INTO opening_hours
            (day_of_week, open_time, close_time, notes)
            VALUES (?, ?, ?, ?)
            """,
            hours_rows,
        )


def get_menu_items(db_path: str) -> List[Dict[str, Any]]:
    """Return all menu items."""

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT item_name, category, description, price,
                   is_vegetarian, is_spicy, is_available
            FROM menu_items
            ORDER BY category, item_name
            """
        ).fetchall()

    return [dict(row) for row in rows]


def search_menu_items(db_path: str, query: str) -> List[Dict[str, Any]]:
    """Search menu items using simple LIKE search."""

    tokens = [
        token.strip().lower()
        for token in query.split()
        if len(token.strip()) >= 3
    ]

    if not tokens:
        return get_menu_items(db_path)

    where_clauses = []
    params: List[str] = []

    for token in tokens[:6]:
        where_clauses.append(
            """
            (
                LOWER(item_name) LIKE ?
                OR LOWER(description) LIKE ?
                OR LOWER(category) LIKE ?
            )
            """
        )

        wildcard = f"%{token}%"
        params.extend([wildcard, wildcard, wildcard])

    sql = (
        """
        SELECT item_name, category, description, price,
               is_vegetarian, is_spicy, is_available
        FROM menu_items
        WHERE
        """
        + " OR ".join(where_clauses)
        + " ORDER BY category, item_name"
    )

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()

    return [dict(row) for row in rows]


def get_restaurant_details_and_hours(
    db_path: str,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Return restaurant details and opening hours."""

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        details_row = conn.execute(
            """
            SELECT name, address, phone, email, website
            FROM restaurant_details
            WHERE id = 1
            """
        ).fetchone()

        hours_rows = conn.execute(
            """
            SELECT day_of_week, open_time, close_time, notes
            FROM opening_hours
            ORDER BY id
            """
        ).fetchall()

    details = dict(details_row) if details_row else {}
    hours = [dict(row) for row in hours_rows]

    return details, hours


def book_reservation(
    db_path: str,
    customer_name: str,
    reservation_date: str,
    reservation_time: str,
    party_size: int,
    contact: str = "",
) -> int:
    """Create a new reservation and return the reservation ID."""

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reservations
            (customer_name, reservation_date, reservation_time, party_size, contact, status)
            VALUES (?, ?, ?, ?, ?, 'booked')
            """,
            (
                customer_name,
                reservation_date,
                reservation_time,
                party_size,
                contact,
            ),
        )

        reservation_id = cursor.lastrowid

    return int(reservation_id)


def cancel_reservation(db_path: str, reservation_id: int) -> bool:
    """Cancel a reservation by ID. Return True if a row was updated."""

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE reservations
            SET status = 'cancelled'
            WHERE id = ? AND status = 'booked'
            """,
            (reservation_id,),
        )

        return cursor.rowcount > 0


def get_reservations(db_path: str) -> List[Dict[str, Any]]:
    """Return all reservations."""

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            """
            SELECT id, customer_name, reservation_date, reservation_time,
                   party_size, contact, status, created_at
            FROM reservations
            ORDER BY id
            """
        ).fetchall()

    return [dict(row) for row in rows]


if __name__ == "__main__":
    db = "restaurant.sqlite"

    initialize_database(db)

    print("Database created successfully.")
    print(f"Menu items: {len(get_menu_items(db))}")

    test_id = book_reservation(
        db_path=db,
        customer_name="Test Customer",
        reservation_date="2026-08-01",
        reservation_time="20:00",
        party_size=2,
        contact="test@example.com",
    )

    print(f"Test reservation created with ID: {test_id}")

    cancelled = cancel_reservation(db, test_id)
    print(f"Test reservation cancelled: {cancelled}")

    print("All reservations:")
    for reservation in get_reservations(db):
        print(reservation)