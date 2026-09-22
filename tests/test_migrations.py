import sqlite3

from migrations import get_schema_version, run_migrations


def test_migration_upgrades_old_database(tmp_path):
    database_path = tmp_path / "legacy.db"

    connection = sqlite3.connect(database_path)

    connection.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL
        )
    """)

    connection.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL,
            category TEXT,
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    connection.execute("""
        INSERT INTO users (
            username,
            hashed_password
        )
        VALUES (?, ?)
    """, (
        "old_user",
        "old_hash"
    ))

    connection.execute("""
        INSERT INTO transactions (
            user_id,
            amount,
            category,
            description
        )
        VALUES (?, ?, ?, ?)
    """, (
        1,
        100,
        "Food",
        "Old transaction"
    ))

    connection.commit()

    run_migrations(connection)

    assert get_schema_version(connection) == 1

    cursor = connection.execute("""
        PRAGMA table_info(transactions)
    """)

    columns = {
        row[1]
        for row in cursor.fetchall()
    }

    assert "transaction_type" in columns
    assert "transaction_date" in columns

    cursor = connection.execute("""
        SELECT
            user_id,
            amount,
            category,
            description,
            transaction_type,
            transaction_date
        FROM transactions
    """)

    row = cursor.fetchone()

    assert row == (
        1,
        100,
        "Food",
        "Old transaction",
        "expense",
        "1970-01-01"
    )

    connection.close()


def test_migration_is_safe_to_run_twice(tmp_path):
    database_path = tmp_path / "database.db"

    connection = sqlite3.connect(database_path)

    run_migrations(connection)
    run_migrations(connection)

    assert get_schema_version(connection) == 1

    connection.close()