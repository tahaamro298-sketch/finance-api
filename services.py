from database import (
    create_user,
    get_user_by_username,
    create_transaction,
    get_all_transactions,
    get_transaction_by_id,
    update_transaction,
    delete_transaction
)

from auth import (
    hash_password,
    verify_password,
    create_access_token
)

from models import Transaction


# Register a new user
def register_user(
    username,
    password,
    connection
):
    existing_user = get_user_by_username(
        username,
        connection
    )

    if existing_user is not None:
        return None

    hashed_password = hash_password(password)

    user_id = create_user(
        username,
        hashed_password,
        connection
    )

    return user_id


# Authenticate a user and create an access token
def authenticate_user(
    username,
    password,
    connection
):
    user = get_user_by_username(
        username,
        connection
    )

    if user is None:
        return None

    if not verify_password(
        password,
        user[2]
    ):
        return None

    return create_access_token(user[0])


# Convert a database row into a Transaction response
def transaction_from_row(row):
    return Transaction(
        id=row[0],
        user_id=row[1],
        amount=row[2],
        category=row[3],
        description=row[4]
    )


# Create a transaction for a user
def create_user_transaction(
    user_id,
    amount,
    category,
    description,
    connection
):
    transaction_id = create_transaction(
        user_id,
        amount,
        category,
        description,
        connection
    )

    row = get_transaction_by_id(
        transaction_id,
        user_id,
        connection
    )

    return transaction_from_row(row)


# Get all transactions for a user
def get_user_transactions(
    user_id,
    connection
):
    rows = get_all_transactions(
        user_id,
        connection
    )

    return [
        transaction_from_row(row)
        for row in rows
    ]


# Get one transaction for a user
def get_user_transaction(
    transaction_id,
    user_id,
    connection
):
    row = get_transaction_by_id(
        transaction_id,
        user_id,
        connection
    )

    if row is None:
        return None

    return transaction_from_row(row)


# Update a user's transaction
def update_user_transaction(
    transaction_id,
    user_id,
    amount,
    category,
    description,
    connection
):
    rows_updated = update_transaction(
        transaction_id,
        user_id,
        amount,
        category,
        description,
        connection
    )

    if rows_updated == 0:
        return None

    row = get_transaction_by_id(
        transaction_id,
        user_id,
        connection
    )

    return transaction_from_row(row)


# Delete a user's transaction
def delete_user_transaction(
    transaction_id,
    user_id,
    connection
):
    return delete_transaction(
        transaction_id,
        user_id,
        connection
    )