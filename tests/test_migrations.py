import os
from datetime import date

import psycopg
import pytest
from dotenv import load_dotenv

from migrations import (
    get_schema_version,
    run_migrations
)


load_dotenv()


TEST_DATABASE = "finance_test"


def get_test_connection():
    return psycopg.connect(
        host=os.getenv("DATABASE_HOST"),
        port=os.getenv("DATABASE_PORT"),
        dbname=TEST_DATABASE,
        user=os.getenv("DATABASE_USER"),
        password=os.getenv("DATABASE_PASSWORD")
    )


@pytest.fixture(autouse=True)
def reset_database():
    connection = get_test_connection()

    try:
        connection.execute("""
            DROP TABLE IF EXISTS transactions CASCADE
        """)

        connection.execute("""
            DROP TABLE IF EXISTS users CASCADE
        """)

        connection.execute("""
            DROP TABLE IF EXISTS schema_version CASCADE
        """)

        connection.commit()
    finally:
        connection.close()


def test_migration_upgrades_old_database():
    connection = get_test_connection()

    try:
        # Create the old transaction schema
        connection.execute("""
            CREATE TABLE users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount DOUBLE PRECISION,
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
            VALUES (%s, %s)
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
            VALUES (%s, %s, %s, %s)
        """, (
            1,
            100,
            "Food",
            "Old transaction"
        ))

        connection.commit()

        # Run migrations
        run_migrations(connection)

        assert get_schema_version(connection) == 1

        cursor = connection.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
            AND table_name = 'transactions'
        """)

        columns = {
            row[0]
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
            date(1970, 1, 1)
        )

    finally:
        connection.close()


def test_migration_is_safe_to_run_twice():
    connection = get_test_connection()

    try:
        run_migrations(connection)
        run_migrations(connection)

        assert get_schema_version(connection) == 1

    finally:
        connection.close()