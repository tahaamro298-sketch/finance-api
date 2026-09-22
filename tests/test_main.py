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

    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 0

    items = data["items"]

    assert len(items) == 1
    assert items[0]["user_id"] == 1
    assert items[0]["transaction_type"] == "expense"
    assert items[0]["transaction_date"] == "2026-09-19"


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

    data = response.json()["items"]

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

    data = response.json()["items"]

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

    data = response.json()["items"]

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

    data = response.json()["items"]

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

    data = response.json()["items"]

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

    data = response.json()["items"]

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


# -------------------------
# Financial summary tests
# -------------------------

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


def test_transaction_summary_date_from():
    register_user("summary_user")

    headers = get_auth_headers("summary_user")

    client.post(
        "/transactions",
        json={
            "amount": 1000,
            "category": "Salary",
            "description": "Old income",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 500,
            "category": "Salary",
            "description": "Recent income",
            "transaction_type": "income",
            "transaction_date": "2026-09-15"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/summary?date_from=2026-09-10",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == {
        "total_income": 500.0,
        "total_expenses": 0.0,
        "balance": 500.0,
        "transaction_count": 1
    }


def test_transaction_summary_date_to():
    register_user("summary_user")

    headers = get_auth_headers("summary_user")

    client.post(
        "/transactions",
        json={
            "amount": 1000,
            "category": "Salary",
            "description": "Early income",
            "transaction_type": "income",
            "transaction_date": "2026-09-05"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 500,
            "category": "Salary",
            "description": "Late income",
            "transaction_type": "income",
            "transaction_date": "2026-09-20"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/summary?date_to=2026-09-10",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == {
        "total_income": 1000.0,
        "total_expenses": 0.0,
        "balance": 1000.0,
        "transaction_count": 1
    }


def test_transaction_summary_date_range():
    register_user("summary_user")

    headers = get_auth_headers("summary_user")

    client.post(
        "/transactions",
        json={
            "amount": 100,
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
            "amount": 500,
            "category": "Salary",
            "description": "Inside range",
            "transaction_type": "income",
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
        "/transactions/summary?date_from=2026-09-01&date_to=2026-09-30",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == {
        "total_income": 500.0,
        "total_expenses": 0.0,
        "balance": 500.0,
        "transaction_count": 1
    }


# -------------------------
# Category summary tests
# -------------------------

def test_category_summary():
    register_user("category_user")

    headers = get_auth_headers("category_user")

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
            "amount": 50,
            "category": "Food",
            "description": "Lunch",
            "transaction_type": "expense",
            "transaction_date": "2026-09-02"
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
            "transaction_date": "2026-09-03"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 5000,
            "category": "Salary",
            "description": "Monthly salary",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/category-summary",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == [
        {
            "category": "Transport",
            "total": 200.0
        },
        {
            "category": "Food",
            "total": 150.0
        }
    ]


def test_category_summary_date_range():
    register_user("category_user")

    headers = get_auth_headers("category_user")

    client.post(
        "/transactions",
        json={
            "amount": 100,
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
            "amount": 300,
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
            "category": "Transport",
            "description": "Inside range",
            "transaction_type": "expense",
            "transaction_date": "2026-09-20"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 500,
            "category": "Shopping",
            "description": "After range",
            "transaction_type": "expense",
            "transaction_date": "2026-10-01"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/category-summary?date_from=2026-09-01&date_to=2026-09-30",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == [
        {
            "category": "Food",
            "total": 300.0
        },
        {
            "category": "Transport",
            "total": 200.0
        }
    ]


def test_category_summary_only_includes_own_transactions():
    register_user("category_first")
    register_user("category_second")

    first_headers = get_auth_headers("category_first")
    second_headers = get_auth_headers("category_second")

    client.post(
        "/transactions",
        json={
            "amount": 100,
            "category": "Food",
            "description": "First user food",
            "transaction_type": "expense",
            "transaction_date": "2026-09-01"
        },
        headers=first_headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 500,
            "category": "Shopping",
            "description": "Second user shopping",
            "transaction_type": "expense",
            "transaction_date": "2026-09-01"
        },
        headers=second_headers
    )

    first_response = client.get(
        "/transactions/category-summary",
        headers=first_headers
    )

    second_response = client.get(
        "/transactions/category-summary",
        headers=second_headers
    )

    assert first_response.json() == [
        {
            "category": "Food",
            "total": 100.0
        }
    ]

    assert second_response.json() == [
        {
            "category": "Shopping",
            "total": 500.0
        }
    ]


# -------------------------
# Monthly summary tests
# -------------------------

def test_monthly_summary():
    register_user("monthly_user")

    headers = get_auth_headers("monthly_user")

    client.post(
        "/transactions",
        json={
            "amount": 3000,
            "category": "Salary",
            "description": "September salary",
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
            "description": "September food",
            "transaction_type": "expense",
            "transaction_date": "2026-09-10"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 4000,
            "category": "Salary",
            "description": "October salary",
            "transaction_type": "income",
            "transaction_date": "2026-10-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 1000,
            "category": "Shopping",
            "description": "October shopping",
            "transaction_type": "expense",
            "transaction_date": "2026-10-15"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/monthly-summary",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == [
        {
            "month": "2026-09",
            "total_income": 3000.0,
            "total_expenses": 500.0,
            "balance": 2500.0
        },
        {
            "month": "2026-10",
            "total_income": 4000.0,
            "total_expenses": 1000.0,
            "balance": 3000.0
        }
    ]


def test_monthly_summary_date_range():
    register_user("monthly_user")

    headers = get_auth_headers("monthly_user")

    client.post(
        "/transactions",
        json={
            "amount": 2000,
            "category": "Salary",
            "description": "August salary",
            "transaction_type": "income",
            "transaction_date": "2026-08-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 3000,
            "category": "Salary",
            "description": "September salary",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=headers
    )

    client.post(
        "/transactions",
        json={
            "amount": 4000,
            "category": "Salary",
            "description": "October salary",
            "transaction_type": "income",
            "transaction_date": "2026-10-01"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/monthly-summary?date_from=2026-09-01&date_to=2026-09-30",
        headers=headers
    )

    assert response.status_code == 200

    assert response.json() == [
        {
            "month": "2026-09",
            "total_income": 3000.0,
            "total_expenses": 0.0,
            "balance": 3000.0
        }
    ]


def test_monthly_summary_only_includes_own_transactions():
    register_user("monthly_first")
    register_user("monthly_second")

    first_headers = get_auth_headers("monthly_first")
    second_headers = get_auth_headers("monthly_second")

    client.post(
        "/transactions",
        json={
            "amount": 1000,
            "category": "Salary",
            "description": "First user salary",
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
            "description": "Second user salary",
            "transaction_type": "income",
            "transaction_date": "2026-09-01"
        },
        headers=second_headers
    )

    first_response = client.get(
        "/transactions/monthly-summary",
        headers=first_headers
    )

    second_response = client.get(
        "/transactions/monthly-summary",
        headers=second_headers
    )

    assert first_response.json() == [
        {
            "month": "2026-09",
            "total_income": 1000.0,
            "total_expenses": 0.0,
            "balance": 1000.0
        }
    ]

    assert second_response.json() == [
        {
            "month": "2026-09",
            "total_income": 5000.0,
            "total_expenses": 0.0,
            "balance": 5000.0
        }
    ]


# -------------------------
# Report validation tests
# -------------------------

def test_report_rejects_invalid_date_range():
    register_user("report_user")

    headers = get_auth_headers("report_user")

    endpoints = [
        "/transactions/summary",
        "/transactions/category-summary",
        "/transactions/monthly-summary"
    ]

    for endpoint in endpoints:
        response = client.get(
            f"{endpoint}?date_from=2026-09-30&date_to=2026-09-01",
            headers=headers
        )

        assert response.status_code == 400

        assert response.json() == {
            "error": "bad_request",
            "message": "date_from cannot be after date_to"
        }


# -------------------------
# Pagination tests
# -------------------------

def test_transaction_pagination():
    register_user("pagination_user")

    headers = get_auth_headers("pagination_user")

    for day in range(1, 6):
        client.post(
            "/transactions",
            json={
                "amount": day * 10,
                "category": "Food",
                "description": f"Transaction {day}",
                "transaction_type": "expense",
                "transaction_date": f"2026-09-{day:02d}"
            },
            headers=headers
        )

    response = client.get(
        "/transactions?limit=2&offset=2",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2

    assert len(data["items"]) == 2

    assert data["items"][0]["id"] == 3
    assert data["items"][1]["id"] == 2


def test_transaction_pagination_defaults():
    register_user("pagination_user")

    headers = get_auth_headers("pagination_user")

    response = client.get(
        "/transactions",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_transaction_pagination_invalid_limit():
    register_user("pagination_user")

    headers = get_auth_headers("pagination_user")

    response = client.get(
        "/transactions?limit=101",
        headers=headers
    )

    assert response.status_code == 422


def test_transaction_pagination_invalid_offset():
    register_user("pagination_user")

    headers = get_auth_headers("pagination_user")

    response = client.get(
        "/transactions?offset=-1",
        headers=headers
    )

    assert response.status_code == 422


def test_transaction_pagination_with_category_filter():
    register_user("pagination_filter_user")

    headers = get_auth_headers("pagination_filter_user")

    transactions = [
        ("Food", "2026-09-01"),
        ("Food", "2026-09-02"),
        ("Food", "2026-09-03"),
        ("Shopping", "2026-09-04"),
        ("Shopping", "2026-09-05")
    ]

    for index, (category, transaction_date) in enumerate(
        transactions,
        start=1
    ):
        client.post(
            "/transactions",
            json={
                "amount": index * 10,
                "category": category,
                "description": f"Transaction {index}",
                "transaction_type": "expense",
                "transaction_date": transaction_date
            },
            headers=headers
        )

    response = client.get(
        "/transactions?category=Food&limit=2&offset=2",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 2

    assert len(data["items"]) == 1
    assert data["items"][0]["category"] == "Food"
    assert data["items"][0]["description"] == "Transaction 1"

def test_bad_request_error_format():
    register_user("error_user")

    response = client.post(
        "/register",
        json={
            "username": "error_user",
            "password": "password123"
        }
    )

    assert response.status_code == 400

    assert response.json() == {
        "error": "bad_request",
        "message": "Username already exists"
    }

def test_unauthorized_error_format():
    response = client.get("/transactions")

    assert response.status_code == 401

    data = response.json()

    assert data["error"] == "unauthorized"
    assert data["message"] == "Not authenticated"

    assert "WWW-Authenticate" in response.headers
    assert response.headers["WWW-Authenticate"] == "Bearer"

def test_not_found_error_format():
    register_user("not_found_user")

    headers = get_auth_headers("not_found_user")

    response = client.get(
        "/transactions/999",
        headers=headers
    )

    assert response.status_code == 404

    assert response.json() == {
        "error": "not_found",
        "message": "Transaction not found"
    }

def test_validation_error_format():
    register_user("validation_user")

    headers = get_auth_headers("validation_user")

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

    data = response.json()

    assert data["error"] == "validation_error"
    assert data["message"] == "Request validation failed"
    assert isinstance(data["details"], list)
    assert len(data["details"]) > 0