import sqlite3

import pytest
from fastapi.testclient import TestClient
from main import app, get_db


# Use a separate database connection for automated tests
def override_get_db():
    connection = sqlite3.connect("test_finance.db")

    try:
        yield connection
    finally:
        connection.close()


# Create the test database table if it does not exist
connection = sqlite3.connect("test_finance.db")

connection.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    amount REAL,
    category TEXT,
    description TEXT
)
""")

connection.commit()
connection.close()


# Tell FastAPI to use the test database instead of the real database
app.dependency_overrides[get_db] = override_get_db


# Clear test data before every test so tests remain independent
@pytest.fixture(autouse=True)
def clear_test_database():
    connection = sqlite3.connect("test_finance.db")

    connection.execute("DELETE FROM transactions")

    connection.commit()
    connection.close()


client = TestClient(app)


def test_home():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == "Hello"


def test_create_transaction_invalid_amount():
    response = client.post(
        "/transactions",
        json={
            "amount": -10,
            "category": "Food",
            "description": "Lunch"
        }
    )

    assert response.status_code == 422


def test_get_transaction_not_found():
    response = client.get("/transactions/999999")

    assert response.status_code == 404


def test_create_transaction():
    response = client.post(
        "/transactions",
        json={
            "amount": 25,
            "category": "Food",
            "description": "Lunch"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["amount"] == 25
    assert data["category"] == "Food"
    assert data["description"] == "Lunch"
    assert "id" in data


def test_get_transactions():
    response = client.get("/transactions")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 0


def test_get_transaction():
    create_response = client.post(
        "/transactions",
        json={
            "amount": 40,
            "category": "Transport",
            "description": "Taxi"
        }
    )

    transaction_id = create_response.json()["id"]

    response = client.get(f"/transactions/{transaction_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == transaction_id
    assert data["amount"] == 40
    assert data["category"] == "Transport"
    assert data["description"] == "Taxi"


def test_update_transaction():
    create_response = client.post(
        "/transactions",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Lunch"
        }
    )

    transaction_id = create_response.json()["id"]

    response = client.put(
        f"/transactions/{transaction_id}",
        json={
            "amount": 75,
            "category": "Restaurant",
            "description": "Dinner"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == transaction_id
    assert data["amount"] == 75
    assert data["category"] == "Restaurant"
    assert data["description"] == "Dinner"


def test_delete_transaction():
    create_response = client.post(
        "/transactions",
        json={
            "amount": 30,
            "category": "Shopping",
            "description": "Shoes"
        }
    )

    transaction_id = create_response.json()["id"]

    response = client.delete(f"/transactions/{transaction_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Transaction deleted successfully"

    get_response = client.get(f"/transactions/{transaction_id}")

    assert get_response.status_code == 404

def test_update_transaction_not_found():
    response = client.put(
        "/transactions/999999",
        json={
            "amount": 50,
            "category": "Food",
            "description": "Lunch"
        }
    )

    assert response.status_code == 404

def test_delete_transaction_not_found():
    response = client.delete("/transactions/999999")

    assert response.status_code == 404

def test_create_transaction_empty_category():
    response = client.post(
        "/transactions",
        json={
            "amount": 20,
            "category": "",
            "description": "Lunch"
        }
    )

    assert response.status_code == 422

def test_create_transaction_category_too_long():
    response = client.post(
        "/transactions",
        json={
            "amount": 20,
            "category": "A" * 51,
            "description": "Lunch"
        }
    )

    assert response.status_code == 422