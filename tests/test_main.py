import sqlite3

import pytest
from fastapi.testclient import TestClient

from main import app, get_db


TEST_DATABASE = "test_finance.db"


# Create a fresh test database connection
def get_test_connection():
    connection = sqlite3.connect(TEST_DATABASE)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# Create the test database schema
def create_test_schema():
    connection = get_test_connection()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        amount REAL,
        category TEXT,
        description TEXT,
        transaction_type TEXT NOT NULL,
        transaction_date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    connection.commit()
    connection.close()


# Replace the application's database with the test database
def override_get_db():
    connection = get_test_connection()

    try:
        yield connection
    finally:
        connection.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


# Reset test data before every test
@pytest.fixture(autouse=True)
def reset_database():
    create_test_schema()

    connection = get_test_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM users")

    connection.commit()
    connection.close()


# -------------------------
# Basic API tests
# -------------------------

def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == "Hello"


def test_invalid_transaction_amount():
    register_user("amro")

    headers = get_auth_headers("amro")

    response = client.post(
        "/transactions",
        json={
            "amount": 0,
            "category": "Food",
            "description": "Invalid amount",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=headers
    )

    assert response.status_code == 422


def test_invalid_transaction_type():
    register_user("amro")

    headers = get_auth_headers("amro")

    response = client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "salary",
            "transaction_date": "2026-09-19"
        },
        headers=headers
    )

    assert response.status_code == 422


def test_invalid_transaction_date():
    register_user("amro")

    headers = get_auth_headers("amro")

    response = client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "not-a-date"
        },
        headers=headers
    )

    assert response.status_code == 422


def test_register_user():
    response = client.post(
        "/register",
        json={
            "username": "amro",
            "password": "password123"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["username"] == "amro"


def test_duplicate_username():
    client.post(
        "/register",
        json={
            "username": "amro",
            "password": "password123"
        }
    )

    response = client.post(
        "/register",
        json={
            "username": "amro",
            "password": "password123"
        }
    )

    assert response.status_code == 400


def test_short_password():
    response = client.post(
        "/register",
        json={
            "username": "amro",
            "password": "short"
        }
    )

    assert response.status_code == 422


# -------------------------
# Authentication tests
# -------------------------

def register_user(username):
    return client.post(
        "/register",
        json={
            "username": username,
            "password": "password123"
        }
    )


def login_user(username):
    response = client.post(
        "/login",
        data={
            "username": username,
            "password": "password123"
        }
    )

    return response


def get_auth_headers(username):
    response = login_user(username)

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def test_login():
    register_user("amro")

    response = login_user("amro")

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_wrong_password():
    register_user("amro")

    response = client.post(
        "/login",
        data={
            "username": "amro",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401


def test_unauthenticated_transactions():
    response = client.get("/transactions")

    assert response.status_code == 401


# -------------------------
# Authenticated transaction tests
# -------------------------

def test_create_transaction_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    response = client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["user_id"] == 1
    assert data["amount"] == 25.5
    assert data["transaction_type"] == "expense"
    assert data["transaction_date"] == "2026-09-19"


def test_get_transactions_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=headers
    )

    response = client.get(
        "/transactions",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["user_id"] == 1
    assert data[0]["transaction_type"] == "expense"
    assert data[0]["transaction_date"] == "2026-09-19"


# -------------------------
# Filtering tests
# -------------------------

def test_filter_transactions_by_type():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 1000,
            "category": "Salary",
            "description": "Monthly salary",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-02"
        },
        headers=headers
    )

    response = client.get(
        "/transactions?transaction_type=expense",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["transaction_type"] == "expense"
    assert data[0]["category"] == "Food"


def test_filter_transactions_by_category():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Shopping",
            "description": "Shoes",
            "transaction_type": "expense",
            "transaction_date": "2026-09-02"
        },
        headers=headers
    )

    response = client.get(
        "/transactions?category=Food",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["category"] == "Food"


def test_filter_transactions_by_type_and_category():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Food",
            "description": "Groceries",
            "transaction_type": "expense",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 200,
            "category": "Food",
            "description": "Freelance payment",
            "transaction_type": "income",
            "transaction_date": "2026-09-02"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 300,
            "category": "Shopping",
            "description": "Laptop accessories",
            "transaction_type": "expense",
            "transaction_date": "2026-09-03"
        },
        headers=headers
    )

    response = client.get(
        "/transactions?transaction_type=expense&category=Food",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["category"] == "Food"
    assert data[0]["transaction_type"] == "expense"


def test_filter_transactions_by_date_from():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Old transaction",
            "transaction_type": "expense",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Food",
            "description": "Recent transaction",
            "transaction_type": "expense",
            "transaction_date": "2026-09-15"
        },
        headers=headers
    )

    response = client.get(
        "/transactions?date_from=2026-09-10",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["transaction_date"] == "2026-09-15"


def test_filter_transactions_by_date_to():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Early transaction",
            "transaction_type": "expense",
            "transaction_date": "2026-09-05"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Food",
            "description": "Late transaction",
            "transaction_type": "expense",
            "transaction_date": "2026-09-20"
        },
        headers=headers
    )

    response = client.get(
        "/transactions?date_to=2026-09-10",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["transaction_date"] == "2026-09-05"


def test_filter_transactions_by_date_range():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Before range",
            "transaction_type": "expense",
            "transaction_date": "2026-08-31"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Food",
            "description": "Inside range",
            "transaction_type": "expense",
            "transaction_date": "2026-09-15"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 200,
            "category": "Shopping",
            "description": "After range",
            "transaction_type": "expense",
            "transaction_date": "2026-10-01"
        },
        headers=headers
    )

    response = client.get(
        "/transactions?date_from=2026-09-01&date_to=2026-09-30",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["transaction_date"] == "2026-09-15"


def test_get_transaction_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/1",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["transaction_type"] == "expense"
    assert data["transaction_date"] == "2026-09-19"


def test_update_transaction_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=headers
    )

    response = client.put(
        "/transactions/1",
        json={
            "amount": 30,
            "category": "Restaurant",
            "description": "Dinner",
            "transaction_type": "expense",
            "transaction_date": "2026-09-20"
        },
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == 30
    assert data["category"] == "Restaurant"
    assert data["transaction_type"] == "expense"
    assert data["transaction_date"] == "2026-09-20"


def test_delete_transaction_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=headers
    )

    response = client.delete(
        "/transactions/1",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json()["message"] == \
        "Transaction deleted successfully"


# -------------------------
# Authorization tests
# -------------------------

def test_user_cannot_access_another_users_transaction():
    register_user("amro")
    register_user("testuser")

    amro_headers = get_auth_headers("amro")
    testuser_headers = get_auth_headers("testuser")

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Shopping",
            "description": "Amro transaction",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=amro_headers
    )

    response = client.get(
        "/transactions/1",
        headers=testuser_headers
    )

    assert response.status_code == 404


def test_user_cannot_update_another_users_transaction():
    register_user("amro")
    register_user("testuser")

    amro_headers = get_auth_headers("amro")
    testuser_headers = get_auth_headers("testuser")

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Shopping",
            "description": "Amro transaction",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=amro_headers
    )

    response = client.put(
        "/transactions/1",
        json={
            "amount": 999,
            "category": "Hacked",
            "description": "Unauthorized",
            "transaction_type": "expense",
            "transaction_date": "2026-09-20"
        },
        headers=testuser_headers
    )

    assert response.status_code == 404


def test_user_cannot_delete_another_users_transaction():
    register_user("amro")
    register_user("testuser")

    amro_headers = get_auth_headers("amro")
    testuser_headers = get_auth_headers("testuser")

    client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Shopping",
            "description": "Amro transaction",
            "transaction_type": "expense",
            "transaction_date": "2026-09-19"
        },
        headers=amro_headers
    )

    response = client.delete(
        "/transactions/1",
        headers=testuser_headers
    )

    assert response.status_code == 404

def test_empty_transaction_summary():
    register_response = client.post(
        "/register",
        json={
            "username": "summary_user",
            "password": "password123"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/login",
        data={
            "username": "summary_user",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = client.get(
        "/transactions/summary",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == {
        "total_income": 0.0,
        "total_expenses": 0.0,
        "balance": 0.0,
        "transaction_count": 0
    }


def test_transaction_summary():
    register_response = client.post(
        "/register",
        json={
            "username": "summary_user",
            "password": "password123"
        }
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/login",
        data={
            "username": "summary_user",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    client.post(
        "/transactions",
        json={
            "amount": 3000,
            "category": "Salary",
            "description": "Monthly salary",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 500,
            "category": "Food",
            "description": "Groceries",
            "transaction_type": "expense",
            "transaction_date": "2026-09-05"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 200,
            "category": "Transport",
            "description": "Taxi",
            "transaction_type": "expense",
            "transaction_date": "2026-09-06"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/summary",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == {
        "total_income": 3000.0,
        "total_expenses": 700.0,
        "balance": 2300.0,
        "transaction_count": 3
    }


def test_unauthenticated_transaction_summary():
    response = client.get("/transactions/summary")

    assert response.status_code == 401

def test_user_summary_only_includes_own_transactions():
    first_user_response = client.post(
        "/register",
        json={
            "username": "summary_first",
            "password": "password123"
        }
    )

    assert first_user_response.status_code == 201

    second_user_response = client.post(
        "/register",
        json={
            "username": "summary_second",
            "password": "password123"
        }
    )

    assert second_user_response.status_code == 201

    first_login = client.post(
        "/login",
        data={
            "username": "summary_first",
            "password": "password123"
        }
    )

    second_login = client.post(
        "/login",
        data={
            "username": "summary_second",
            "password": "password123"
        }
    )

    first_token = first_login.json()["access_token"]
    second_token = second_login.json()["access_token"]

    first_headers = {
        "Authorization": f"Bearer {first_token}"
    }

    second_headers = {
        "Authorization": f"Bearer {second_token}"
    }

    client.post(
        "/transactions",
        json={
            "amount": 1000,
            "category": "Salary",
            "description": "First user income",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=first_headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 5000,
            "category": "Salary",
            "description": "Second user income",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=second_headers
    )

    first_summary = client.get(
        "/transactions/summary",
        headers=first_headers
    )

    second_summary = client.get(
        "/transactions/summary",
        headers=second_headers
    )

    assert first_summary.json() == {
        "total_income": 1000.0,
        "total_expenses": 0.0,
        "balance": 1000.0,
        "transaction_count": 1
    }

    assert second_summary.json() == {
        "total_income": 5000.0,
        "total_expenses": 0.0,
        "balance": 5000.0,
        "transaction_count": 1
    }