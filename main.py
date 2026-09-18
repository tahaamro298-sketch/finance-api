from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from services import (
    register_user,
    authenticate_user,
    create_user_transaction,
    get_user_transactions,
    get_user_transaction,
    update_user_transaction,
    delete_user_transaction
)

from dependencies import (
    get_db,
    get_current_user
)

from models import (
    UserCreate,
    UserResponse,
    Token,
    TransactionCreate,
    Transaction,
    DeleteResponse
)

from services import (
    create_user_transaction,
    get_user_transactions,
    get_user_transaction,
    update_user_transaction,
    delete_user_transaction
)


app = FastAPI()


@app.get("/")
def home():
    return "Hello"


# Register a new user
@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user_endpoint(
    user: UserCreate,
    connection=Depends(get_db)
):
    user_id = register_user(
        user.username,
        user.password,
        connection
    )

    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    return UserResponse(
        id=user_id,
        username=user.username
    )

# Log in a user and return a JWT access token
@app.post("/login", response_model=Token)
def login_user_endpoint(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection=Depends(get_db)
):
    access_token = authenticate_user(
        form_data.username,
        form_data.password,
        connection
    )

    if access_token is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# Create a transaction for the authenticated user
@app.post(
    "/transactions",
    response_model=Transaction,
    status_code=status.HTTP_201_CREATED
)
def create_transaction_endpoint(
    transaction: TransactionCreate,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    return create_user_transaction(
        current_user[0],
        transaction.amount,
        transaction.category,
        transaction.description,
        connection
    )


# Get only the authenticated user's transactions
@app.get("/transactions", response_model=list[Transaction])
def get_transactions(
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    return get_user_transactions(
        current_user[0],
        connection
    )


# Get one transaction belonging to the authenticated user
@app.get(
    "/transactions/{transaction_id}",
    response_model=Transaction
)
def get_transaction(
    transaction_id: int,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    transaction = get_user_transaction(
        transaction_id,
        current_user[0],
        connection
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction


# Update a transaction belonging to the authenticated user
@app.put(
    "/transactions/{transaction_id}",
    response_model=Transaction
)
def update_transaction_endpoint(
    transaction_id: int,
    transaction: TransactionCreate,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    updated_transaction = update_user_transaction(
        transaction_id,
        current_user[0],
        transaction.amount,
        transaction.category,
        transaction.description,
        connection
    )

    if updated_transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return updated_transaction


# Delete a transaction belonging to the authenticated user
@app.delete(
    "/transactions/{transaction_id}",
    response_model=DeleteResponse
)
def delete_transaction_endpoint(
    transaction_id: int,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    rows_deleted = delete_user_transaction(
        transaction_id,
        current_user[0],
        connection
    )

    if rows_deleted == 0:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {
        "message": "Transaction deleted successfully"
    }