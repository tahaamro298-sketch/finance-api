from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import OAuth2PasswordRequestForm

from config import settings
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from dependencies import get_current_user, get_db
from models import (
    CategorySummary,
    DeleteResponse,
    MonthlySummary,
    Summary,
    Token,
    Transaction,
    TransactionCreate,
    TransactionList,
    UserCreate,
    UserResponse,
)
from services import (
    authenticate_user,
    create_user_transaction,
    delete_user_transaction,
    get_user_category_summary,
    get_user_monthly_summary,
    get_user_summary,
    get_user_transaction,
    get_user_transactions,
    register_user,
    update_user_transaction,
)


app = FastAPI()


app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.allowed_hosts,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
)


@app.middleware("http")
async def add_security_headers(
    request: Request,
    call_next
):
    response = await call_next(request)

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    return response


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
):
    error_types = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed"
    }

    error_type = error_types.get(
        exc.status_code,
        "http_error"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": error_type,
            "message": str(exc.detail)
        },
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "details": jsonable_encoder(exc.errors())
        }
    )


def validate_date_range(
    date_from: date | None,
    date_to: date | None
):
    if (
        date_from is not None
        and date_to is not None
        and date_from > date_to
    ):
        raise HTTPException(
            status_code=400,
            detail="date_from cannot be after date_to"
        )


@app.get("/")
def home():
    return "Hello"


@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
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
            detail="Username already exists"
        )

    return {
        "id": user_id,
        "username": user.username
    }


@app.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    connection=Depends(get_db)
):
    token = authenticate_user(
        form_data.username,
        form_data.password,
        connection
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


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
        transaction.transaction_type,
        transaction.transaction_date,
        connection
    )


@app.get(
    "/transactions",
    response_model=TransactionList
)
def get_transactions(
    transaction_type: str | None = None,
    category: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    return get_user_transactions(
        current_user[0],
        connection,
        transaction_type,
        category,
        date_from,
        date_to,
        limit,
        offset
    )


@app.get(
    "/transactions/summary",
    response_model=Summary
)
def get_transactions_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    validate_date_range(
        date_from,
        date_to
    )

    return get_user_summary(
        current_user[0],
        connection,
        date_from,
        date_to
    )


@app.get(
    "/transactions/category-summary",
    response_model=list[CategorySummary]
)
def get_category_summary_report(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    validate_date_range(
        date_from,
        date_to
    )

    return get_user_category_summary(
        current_user[0],
        connection,
        date_from,
        date_to
    )


@app.get(
    "/transactions/monthly-summary",
    response_model=list[MonthlySummary]
)
def get_monthly_summary_report(
    date_from: date | None = None,
    date_to: date | None = None,
    current_user=Depends(get_current_user),
    connection=Depends(get_db)
):
    validate_date_range(
        date_from,
        date_to
    )

    return get_user_monthly_summary(
        current_user[0],
        connection,
        date_from,
        date_to
    )


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
        transaction.transaction_type,
        transaction.transaction_date,
        connection
    )

    if updated_transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return updated_transaction


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