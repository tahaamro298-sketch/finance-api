from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, Field

from database import (
    get_connection,
    create_user,
    get_user_by_username,
    get_user_by_id,
    create_transaction,
    get_all_transactions,
    get_transaction_by_id,
    update_transaction,
    delete_transaction
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)


app = FastAPI()


# Read Bearer tokens from the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Provide a database connection to each request
def get_db():
    connection = get_connection()

    try:
        yield connection
    finally:
        connection.close()


# Decode the JWT and return the authenticated user
def get_current_user(
    token: str = Depends(oauth2_scheme),
    connection=Depends(get_db)
):
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = get_user_by_id(
        user_id,
        connection
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


# Convert a database row into a Transaction response
def transaction_from_row(row):
    return Transaction(
        id=row[0],
        user_id=row[1],
        amount=row[2],
        category=row[3],
        description=row[4]
    )


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str


# Response returned after a successful login
class Token(BaseModel):
    access_token: str
    token_type: str


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=200)


class Transaction(BaseModel):
    id: int
    user_id: int
    amount: float
    category: str
    description: str


class DeleteResponse(BaseModel):
    message: str


@app.get("/")
def home():
    return "Hello"


# Register a new user
@app.post("/register", response_model=UserResponse)
def register_user(
    user: UserCreate,
    connection=Depends(get_db)
):
    existing_user = get_user_by_username(
        user.username,
        connection
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )

    hashed_password = hash_password(user.password)

    user_id = create_user(
        user.username,
        hashed_password,
        connection
    )

    return UserResponse(
        id=user_id,
        username=user.username
    )


# Log in a user and return a JWT access token
@app.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection=Depends(get_db)
):
    user = get_user_by_username(
        form_data.username,
        connection
    )

    if user is None or not verify_password(
        form_data.password,
        user[2]
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    access_token = create_access_token(user[0])

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# Create a transaction for the authenticated user
@app.post("/transactions", response_model=Transaction)
def create_transaction_endpoint(
    transaction: TransactionCreate,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    transaction_id = create_transaction(
        current_user[0],
        transaction.amount,
        transaction.category,
        transaction.description,
        connection
    )

    row = get_transaction_by_id(
        transaction_id,
        current_user[0],
        connection
    )

    return transaction_from_row(row)


# Get only the authenticated user's transactions
@app.get("/transactions", response_model=list[Transaction])
def get_transactions(
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    rows = get_all_transactions(
        current_user[0],
        connection
    )

    return [
        transaction_from_row(row)
        for row in rows
    ]


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
    row = get_transaction_by_id(
        transaction_id,
        current_user[0],
        connection
    )

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return transaction_from_row(row)


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
    rows_updated = update_transaction(
        transaction_id,
        current_user[0],
        transaction.amount,
        transaction.category,
        transaction.description,
        connection
    )

    if rows_updated == 0:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    row = get_transaction_by_id(
        transaction_id,
        current_user[0],
        connection
    )

    return transaction_from_row(row)


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
    rows_deleted = delete_transaction(
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