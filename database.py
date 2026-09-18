import sqlite3


def get_connection():
    return sqlite3.connect("finance.db")


# Create the transactions table if it does not already exist
connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    amount REAL,
    category TEXT,
    description TEXT
)
""")

connection.commit()
connection.close()


def create_transaction(amount, category, description, connection):

    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transactions (amount, category, description)
        VALUES (?, ?, ?)
    """, (amount, category, description))

    connection.commit()

    transaction_id = cursor.lastrowid

    

    return transaction_id


def get_all_transactions(connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, amount, category, description
        FROM transactions
    """)

    rows = cursor.fetchall()

    return rows


def get_transaction_by_id(transaction_id, connection):
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, amount, category, description
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    row = cursor.fetchone()

    return row


def update_transaction(
    transaction_id,
    amount,
    category,
    description,
    connection
):
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE transactions
        SET amount = ?, category = ?, description = ?
        WHERE id = ?
    """, (
        amount,
        category,
        description,
        transaction_id
    ))

    connection.commit()

    rows_updated = cursor.rowcount

    return rows_updated


def delete_transaction(transaction_id, connection):
    
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    connection.commit()

    rows_deleted = cursor.rowcount

    

    return rows_deleted

