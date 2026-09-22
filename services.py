from database import (
    create_user,
    get_user_by_username,
    create_transaction,
    get_all_transactions,
    count_transactions,
    get_transaction_by_id,
    update_transaction,
    delete_transaction,
    get_transaction_summary,
    get_category_summary,
    get_monthly_summary
)

from auth import (
    hash_password,
    verify_password,
    create_access_token
)

from models import (
    Transaction,
    TransactionList
)


def register_user(username, password, connection):
    existing_user = get_user_by_username(username, connection)

    if existing_user is not None:
        return None

    hashed_password = hash_password(password)

    user_id = create_user(
        username,
        hashed_password,
        connection
    )

    return user_id


def authenticate_user(username, password, connection):
    user = get_user_by_username(
        username,
        connection
    )

    if user is None:
        return None

    if not verify_password(password, user[2]):
        return None

    return create_access_token(user[0])


def transaction_from_row(row):
    return Transaction(
        id=row[0],
        user_id=row[1],
        amount=row[2],
        category=row[3],
        description=row[4],
        transaction_type=row[5],
        transaction_date=row[6]
    )


def create_user_transaction(
    user_id,
    amount,
    category,
    description,
    transaction_type,
    transaction_date,
    connection
):
    transaction_id = create_transaction(
        user_id,
        amount,
        category,
        description,
        transaction_type,
        transaction_date.isoformat(),
        connection
    )

    row = get_transaction_by_id(
        transaction_id,
        user_id,
        connection
    )

    return transaction_from_row(row)


def get_user_transactions(
    user_id,
    connection,
    transaction_type=None,
    category=None,
    date_from=None,
    date_to=None,
    limit=20,
    offset=0
):
    rows = get_all_transactions(
        user_id,
        connection,
        transaction_type,
        category,
        date_from,
        date_to,
        limit,
        offset
    )

    total = count_transactions(
        user_id,
        connection,
        transaction_type,
        category,
        date_from,
        date_to
    )

    transactions = [
        transaction_from_row(row)
        for row in rows
    ]

    return TransactionList(
        items=transactions,
        total=total,
        limit=limit,
        offset=offset
    )


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


def update_user_transaction(
    transaction_id,
    user_id,
    amount,
    category,
    description,
    transaction_type,
    transaction_date,
    connection
):
    rows_updated = update_transaction(
        transaction_id,
        user_id,
        amount,
        category,
        description,
        transaction_type,
        transaction_date.isoformat(),
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


def get_user_summary(
    user_id,
    connection,
    date_from=None,
    date_to=None
):
    row = get_transaction_summary(
        user_id,
        connection,
        date_from,
        date_to
    )

    total_income = row[0]
    total_expenses = row[1]
    transaction_count = row[2]

    balance = total_income - total_expenses

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "transaction_count": transaction_count
    }


def get_user_category_summary(
    user_id,
    connection,
    date_from=None,
    date_to=None
):
    rows = get_category_summary(
        user_id,
        connection,
        date_from,
        date_to
    )

    return [
        {
            "category": row[0],
            "total": row[1]
        }
        for row in rows
    ]


def get_user_monthly_summary(
    user_id,
    connection,
    date_from=None,
    date_to=None
):
    rows = get_monthly_summary(
        user_id,
        connection,
        date_from,
        date_to
    )

    return [
        {
            "month": row[0],
            "total_income": row[1],
            "total_expenses": row[2],
            "balance": row[1] - row[2]
        }
        for row in rows
    ]