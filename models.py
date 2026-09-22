from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    category: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=1, max_length=200)
    transaction_type: Literal["income", "expense"]
    transaction_date: date


class Transaction(BaseModel):
    id: int
    user_id: int
    amount: float
    category: str
    description: str
    transaction_type: Literal["income", "expense"]
    transaction_date: date


class DeleteResponse(BaseModel):
    message: str


class Summary(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    transaction_count: int

class CategorySummary(BaseModel):
    category: str
    total: float

class MonthlySummary(BaseModel):
    month: str
    total_income: float
    total_expenses: float
    balance: float