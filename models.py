from pydantic import BaseModel, Field


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