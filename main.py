from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from database import (
    get_connection,
    create_transaction,
    get_all_transactions,
    get_transaction_by_id,
    update_transaction,
    delete_transaction
)

app = FastAPI()


# Provides a database connection to the route and closes it afterward
def get_db():
    connection = get_connection()
    try:
        yield connection
    finally:
        connection.close()


# Data the client is allowed to send when creating or updating a transaction
class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=200)


# Complete transaction returned by the API
class Transaction(BaseModel):
    id: int
    amount: float
    category: str
    description: str


# Response returned after deleting a transaction
class DeleteResponse(BaseModel):
    message: str


@app.get("/")
def home():
    return "Hello"


@app.post("/transactions", response_model=Transaction)
def create_transaction_endpoint(transaction: TransactionCreate, connection=Depends(get_db)):
    transaction_id = create_transaction(
        transaction.amount,
        transaction.category,
        transaction.description,
        connection
    )

    new_transaction = Transaction(
        id=transaction_id,
        amount=transaction.amount,
        category=transaction.category,
        description=transaction.description
    )

    return new_transaction


@app.get("/transactions", response_model=list[Transaction])
def get_transactions(connection=Depends(get_db)):
    rows = get_all_transactions(connection)

    return [
        Transaction(
            id=row[0],
            amount=row[1],
            category=row[2],
            description=row[3]
        )
        for row in rows
    ]


@app.get("/transactions/{transaction_id}", response_model=Transaction)
def get_transaction(
    transaction_id: int,
    connection=Depends(get_db)
):
    row = get_transaction_by_id(transaction_id, connection)

    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return Transaction(
        id=row[0],
        amount=row[1],
        category=row[2],
        description=row[3]
    )


@app.put("/transactions/{transaction_id}", response_model=Transaction)
def update_transaction_endpoint(
    transaction_id: int,
    transaction: TransactionCreate,
    connection=Depends(get_db)
):
    rows_updated = update_transaction(
        transaction_id,
        transaction.amount,
        transaction.category,
        transaction.description,
        connection
    )

    if rows_updated == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")

    row = get_transaction_by_id(transaction_id, connection)

    if row is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return Transaction(
        id=row[0],
        amount=row[1],
        category=row[2],
        description=row[3]
    )


@app.delete("/transactions/{transaction_id}", response_model=DeleteResponse)
def delete_transaction_endpoint(transaction_id: int, connection=Depends(get_db)):
    rows_deleted = delete_transaction(transaction_id, connection)

    if rows_deleted == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {"message": "Transaction deleted successfully"}

