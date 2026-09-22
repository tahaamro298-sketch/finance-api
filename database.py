import psycopg

from config import settings
from migrations import run_migrations


def get_connection():
    return psycopg.connect(
        host=settings.database_host,
        port=settings.database_port,
        dbname=settings.database_name,
        user=settings.database_user,
        password=settings.database_password
    )


def initialize_database():
    connection = get_connection()
    try:
        run_migrations(connection)
    finally:
        connection.close()


initialize_database()


# -------------------------
# User database operations
# -------------------------

def create_user(username, hashed_password, connection):
    cursor = connection.execute("""
        INSERT INTO users (username, hashed_password)
        VALUES (%s, %s)
        RETURNING id
    """, (
        username,
        hashed_password
    ))

    connection.commit()

    return cursor.fetchone()[0]


def get_user_by_username(username, connection):
    cursor = connection.execute("""
        SELECT id, username, hashed_password
        FROM users
        WHERE username = %s
    """, (username,))

    return cursor.fetchone()


def get_user_by_id(user_id, connection):
    cursor = connection.execute("""
        SELECT id, username, hashed_password
        FROM users
        WHERE id = %s
    """, (user_id,))

    return cursor.fetchone()


# -------------------------
# Transaction query helpers
# -------------------------

def build_transaction_filters(
    user_id,
    transaction_type=None,
    category=None,
    date_from=None,
    date_to=None
):
    query = """
        FROM transactions
        WHERE user_id = %s
    """

    parameters = [user_id]

    # Add an optional transaction-type filter
    if transaction_type is not None:
        query += " AND transaction_type = %s"
        parameters.append(transaction_type)

    # Add an optional category filter
    if category is not None:
        query += " AND category = %s"
        parameters.append(category)

    # Add an optional start-date filter
    if date_from is not None:
        query += " AND transaction_date >= %s"
        parameters.append(date_from)

    # Add an optional end-date filter
    if date_to is not None:
        query += " AND transaction_date <= %s"
        parameters.append(date_to)

    return query, parameters


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
    cursor = connection.execute("""
        INSERT INTO transactions (
            user_id,
            amount,
            category,
            description,
            transaction_type,
            transaction_date
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        user_id,
        amount,
        category,
        description,
        transaction_type,
        transaction_date
    ))

    connection.commit()

    return cursor.fetchone()[0]


def get_all_transactions(
    user_id,
    connection,
    transaction_type=None,
    category=None,
    date_from=None,
    date_to=None,
    limit=20,
    offset=0
):
    filters, parameters = build_transaction_filters(
        user_id,
        transaction_type,
        category,
        date_from,
        date_to
    )

    query = """
        SELECT
            id,
            user_id,
            amount,
            category,
            description,
            transaction_type,
            transaction_date
    """

    query += filters

    # Return newest transactions first
    query += " ORDER BY transaction_date DESC, id DESC"

    # Return only the requested page
    query += " LIMIT %s OFFSET %s"

    parameters.extend([
        limit,
        offset
    ])

    cursor = connection.execute(
        query,
        parameters
    )

    return cursor.fetchall()


def count_transactions(
    user_id,
    connection,
    transaction_type=None,
    category=None,
    date_from=None,
    date_to=None
):
    filters, parameters = build_transaction_filters(
        user_id,
        transaction_type,
        category,
        date_from,
        date_to
    )

    query = "SELECT COUNT(*) " + filters

    cursor = connection.execute(
        query,
        parameters
    )

    return cursor.fetchone()[0]


def get_transaction_by_id(
    transaction_id,
    user_id,
    connection
):
    cursor = connection.execute("""
        SELECT
            id,
            user_id,
            amount,
            category,
            description,
            transaction_type,
            transaction_date
        FROM transactions
        WHERE id = %s AND user_id = %s
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
    cursor = connection.execute("""
        UPDATE transactions
        SET
            amount = %s,
            category = %s,
            description = %s,
            transaction_type = %s,
            transaction_date = %s
        WHERE id = %s AND user_id = %s
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
    cursor = connection.execute("""
        DELETE FROM transactions
        WHERE id = %s AND user_id = %s
    """, (
        transaction_id,
        user_id
    ))

    connection.commit()

    return cursor.rowcount


# -------------------------
# Financial summary operations
# -------------------------

def get_transaction_summary(
    user_id,
    connection,
    date_from=None,
    date_to=None
):
    query = """
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
        WHERE user_id = %s
    """

    parameters = [user_id]

    # Add an optional start-date filter
    if date_from is not None:
        query += " AND transaction_date >= %s"
        parameters.append(date_from)

    # Add an optional end-date filter
    if date_to is not None:
        query += " AND transaction_date <= %s"
        parameters.append(date_to)

    cursor = connection.execute(
        query,
        parameters
    )

    return cursor.fetchone()


def get_category_summary(
    user_id,
    connection,
    date_from=None,
    date_to=None
):
    query = """
        SELECT
            category,
            SUM(amount) AS total
        FROM transactions
        WHERE user_id = %s
        AND transaction_type = 'expense'
    """

    parameters = [user_id]

    # Add an optional start-date filter
    if date_from is not None:
        query += " AND transaction_date >= %s"
        parameters.append(date_from)

    # Add an optional end-date filter
    if date_to is not None:
        query += " AND transaction_date <= %s"
        parameters.append(date_to)

    query += """
        GROUP BY category
        ORDER BY total DESC
    """

    cursor = connection.execute(
        query,
        parameters
    )

    return cursor.fetchall()


def get_monthly_summary(
    user_id,
    connection,
    date_from=None,
    date_to=None
):
    query = """
        SELECT
            SUBSTRING(transaction_date::TEXT FROM 1 FOR 7) AS month,

            COALESCE(SUM(CASE
                WHEN transaction_type = 'income'
                THEN amount
                ELSE 0
            END), 0) AS total_income,

            COALESCE(SUM(CASE
                WHEN transaction_type = 'expense'
                THEN amount
                ELSE 0
            END), 0) AS total_expenses

        FROM transactions
        WHERE user_id = %s
    """

    parameters = [user_id]

    # Add an optional start-date filter
    if date_from is not None:
        query += " AND transaction_date >= %s"
        parameters.append(date_from)

    # Add an optional end-date filter
    if date_to is not None:
        query += " AND transaction_date <= %s"
        parameters.append(date_to)

    query += """
        GROUP BY SUBSTRING(transaction_date::TEXT FROM 1 FOR 7)
        ORDER BY month
    """

    cursor = connection.execute(
        query,
        parameters
    )

    return cursor.fetchall()