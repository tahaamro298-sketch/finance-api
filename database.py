import sqlite3


def get_connection():
    connection = sqlite3.connect("finance.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


connection = get_connection()
cursor = connection.cursor()

# Create the users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL
)
""")

# Create the transactions table
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


# Create a new user and return the generated user ID
def create_user(username, hashed_password, connection):
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (username, hashed_password)
        VALUES (?, ?)
    """, (username, hashed_password))

    connection.commit()

    return cursor.lastrowid


# Find a user by username
def get_user_by_username(username, connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, hashed_password
        FROM users
        WHERE username = ?
    """, (username,))

    return cursor.fetchone()

# Find a user by their ID
def get_user_by_id(user_id, connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, hashed_password
        FROM users
        WHERE id = ?
    """, (user_id,))

    return cursor.fetchone()
    
# Create a transaction for a specific user
def create_transaction(
    user_id,
    amount,
    category,
    description,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions (
            user_id,
            amount,
            category,
            description
        )
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        amount,
        category,
        description
    ))

    connection.commit()

    return cursor.lastrowid


# Get all transactions belonging to a specific user
def get_all_transactions(user_id, connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, user_id, amount, category, description
        FROM transactions
        WHERE user_id = ?
    """, (user_id,))

    return cursor.fetchall()


# Get one transaction belonging to a specific user
def get_transaction_by_id(
    transaction_id,
    user_id,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, user_id, amount, category, description
        FROM transactions
        WHERE id = ? AND user_id = ?
    """, (
        transaction_id,
        user_id
    ))

    return cursor.fetchone()


# Update a transaction belonging to a specific user
def update_transaction(
    transaction_id,
    user_id,
    amount,
    category,
    description,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE transactions
        SET amount = ?, category = ?, description = ?
        WHERE id = ? AND user_id = ?
    """, (
        amount,
        category,
        description,
        transaction_id,
        user_id
    ))

    connection.commit()

    return cursor.rowcount


# Delete a transaction belonging to a specific user
def delete_transaction(
    transaction_id,
    user_id,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE id = ? AND user_id = ?
    """, (
        transaction_id,
        user_id
    ))

    connection.commit()

    return cursor.rowcount