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
            "description": "Invalid amount"
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
            "description": "Lunch"
        },
        headers=headers
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["user_id"] == 1
    assert data["amount"] == 25.5


def test_get_transactions_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch"
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


def test_get_transaction_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch"
        },
        headers=headers
    )

    response = client.get(
        "/transactions/1",
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_update_transaction_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch"
        },
        headers=headers
    )

    response = client.put(
        "/transactions/1",
        json={
            "amount": 30,
            "category": "Restaurant",
            "description": "Dinner"
        },
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == 30
    assert data["category"] == "Restaurant"


def test_delete_transaction_authenticated():
    register_user("amro")

    headers = get_auth_headers("amro")

    client.post(
        "/transactions",
        json={
            "amount": 25.5,
            "category": "Food",
            "description": "Lunch"
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
            "description": "Amro transaction"
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
            "description": "Amro transaction"
        },
        headers=amro_headers
    )

    response = client.put(
        "/transactions/1",
        json={
            "amount": 999,
            "category": "Hacked",
            "description": "Unauthorized"
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
            "description": "Amro transaction"
        },
        headers=amro_headers
    )

    response = client.delete(
        "/transactions/1",
        headers=testuser_headers
    )

    assert response.status_code == 404