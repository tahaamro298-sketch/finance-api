import sqlite3


def get_connection():
    connection = sqlite3.connect("finance.db")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# Create the database tables
connection = get_connection()
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


# -------------------------
# User database operations
# -------------------------

def create_user(username, hashed_password, connection):
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (username, hashed_password)
        VALUES (?, ?)
    """, (
        username,
        hashed_password
    ))

    connection.commit()

    return cursor.lastrowid


def get_user_by_username(username, connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, hashed_password
        FROM users
        WHERE username = ?
    """, (username,))

    return cursor.fetchone()


def get_user_by_id(user_id, connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, username, hashed_password
        FROM users
        WHERE id = ?
    """, (user_id,))

    return cursor.fetchone()


# -------------------------
# Transaction database operations
# -------------------------

def create_transaction(
    user_id,
    amount,
    category,
    description,
    transaction_type,
    transaction_date,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions (
            user_id,
            amount,
            category,
            description,
            transaction_type,
            transaction_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        amount,
        category,
        description,
        transaction_type,
        transaction_date
    ))

    connection.commit()

    return cursor.lastrowid


def get_all_transactions(
    user_id,
    connection,
    transaction_type=None,
    category=None,
    date_from=None,
    date_to=None
):
    cursor = connection.cursor()

    query = """
        SELECT
            id,
            user_id,
            amount,
            category,
            description,
            transaction_type,
            transaction_date
        FROM transactions
        WHERE user_id = ?
    """

    parameters = [user_id]

    # Add an optional transaction-type filter
    if transaction_type is not None:
        query += " AND transaction_type = ?"
        parameters.append(transaction_type)

    # Add an optional category filter
    if category is not None:
        query += " AND category = ?"
        parameters.append(category)

    # Add an optional start-date filter
    if date_from is not None:
        query += " AND transaction_date >= ?"
        parameters.append(date_from.isoformat())

    # Add an optional end-date filter
    if date_to is not None:
        query += " AND transaction_date <= ?"
        parameters.append(date_to.isoformat())

    # Return newest transactions first
    query += " ORDER BY transaction_date DESC, id DESC"

    cursor.execute(
        query,
        parameters
    )

    return cursor.fetchall()


def get_transaction_by_id(
    transaction_id,
    user_id,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            user_id,
            amount,
            category,
            description,
            transaction_type,
            transaction_date
        FROM transactions
        WHERE id = ? AND user_id = ?
    """, (
        transaction_id,
        user_id
    ))

    return cursor.fetchone()


def update_transaction(
    transaction_id,
    user_id,
    amount,
    category,
    description,
    transaction_type,
    transaction_date,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE transactions
        SET
            amount = ?,
            category = ?,
            description = ?,
            transaction_type = ?,
            transaction_date = ?
        WHERE id = ? AND user_id = ?
    """, (
        amount,
        category,
        description,
        transaction_type,
        transaction_date,
        transaction_id,
        user_id
    ))

    connection.commit()

    return cursor.rowcount


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

def get_transaction_summary(user_id, connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COALESCE(SUM(CASE
                WHEN transaction_type = 'income'
                THEN amount
                ELSE 0
            END), 0),

            COALESCE(SUM(CASE
                WHEN transaction_type = 'expense'
                THEN amount
                ELSE 0
            END), 0),

            COUNT(*)

        FROM transactions
        WHERE user_id = ?
    """, (user_id,))

    return cursor.fetchone()