# Finance API

A RESTful finance management API built with **Python, FastAPI, SQLite, JWT authentication, Pydantic, and pytest**.

The project allows users to create accounts, log in securely, manage their own financial transactions, filter transactions, and view a financial summary.

## Features

* User registration and login
* Secure password hashing with Argon2
* JWT-based authentication
* Protected transaction endpoints
* User-specific transaction ownership
* Create, read, update, and delete transactions
* Income and expense transaction types
* Transaction dates
* Filter transactions by:

  * Transaction type
  * Category
  * Start date
  * End date
* Financial summary with:

  * Total income
  * Total expenses
  * Balance
  * Transaction count
* Pydantic request and response validation
* SQLite database
* Dependency injection for database connections and authentication
* Service-layer architecture
* Automated testing with pytest
* 28 automated tests

## Technologies

* **Python 3.14**
* **FastAPI**
* **Uvicorn**
* **SQLite**
* **Pydantic**
* **pwdlib**
* **Argon2**
* **PyJWT**
* **python-dotenv**
* **pytest**
* **HTTPX**

## Project Structure

```text
finance-api/
│
├── main.py
├── models.py
├── database.py
├── services.py
├── dependencies.py
├── auth.py
├── finance.db
├── test_finance.db
├── .env
├── .gitignore
├── README.md
│
└── tests/
    └── test_main.py
```

### File responsibilities

**`main.py`**

Contains the FastAPI application and HTTP endpoints.

**`models.py`**

Contains Pydantic models used for request validation and API responses.

**`database.py`**

Contains SQLite database setup and database operations.

**`services.py`**

Contains business logic between the API layer and database layer.

**`dependencies.py`**

Contains reusable FastAPI dependencies such as database connections and the current authenticated user.

**`auth.py`**

Contains password hashing and JWT authentication logic.

**`tests/test_main.py`**

Contains automated API tests.

## Architecture

The application follows a layered structure:

```text
HTTP Request
     ↓
main.py
     ↓
services.py
     ↓
database.py
     ↓
SQLite
```

Supporting components:

```text
models.py
    ↓
Request / Response validation

auth.py
    ↓
Password hashing / JWT

dependencies.py
    ↓
Database connection / Current user
```

This separation keeps API routes, business logic, authentication, validation, and database operations organized independently.

## Authentication

The API uses:

* **Argon2** for password hashing
* **JWT Bearer tokens** for authentication

Passwords are never stored as plain text.

After logging in successfully, the API returns an access token:

```json
{
  "access_token": "your-jwt-token",
  "token_type": "bearer"
}
```

Protected endpoints require:

```text
Authorization: Bearer <token>
```

Transactions are associated with the authenticated user, so users can only access their own transactions.

## API Endpoints

### Root

```http
GET /
```

Returns a simple response confirming that the API is running.

---

### Register

```http
POST /register
```

Creates a new user account.

Example request:

```json
{
  "username": "amro",
  "password": "password123"
}
```

Example response:

```json
{
  "id": 1,
  "username": "amro"
}
```

Returns:

```text
201 Created
```

---

### Login

```http
POST /login
```

Authenticates a user and returns a JWT access token.

The endpoint uses OAuth2 password-form data.

Example form data:

```text
username=amro
password=password123
```

Example response:

```json
{
  "access_token": "your-jwt-token",
  "token_type": "bearer"
}
```

---

## Transactions

All transaction endpoints require authentication.

### Create Transaction

```http
POST /transactions
```

Example request:

```json
{
  "amount": 250.5,
  "category": "Food",
  "description": "Dinner",
  "transaction_type": "expense",
  "transaction_date": "2026-09-19"
}
```

Example response:

```json
{
  "id": 1,
  "user_id": 1,
  "amount": 250.5,
  "category": "Food",
  "description": "Dinner",
  "transaction_type": "expense",
  "transaction_date": "2026-09-19"
}
```

Returns:

```text
201 Created
```

### Get All Transactions

```http
GET /transactions
```

Returns all transactions belonging to the authenticated user.

Transactions are returned with the newest transaction dates first.

---

### Filter Transactions

The transaction list endpoint supports optional query parameters.

#### By transaction type

```http
GET /transactions?transaction_type=expense
```

Possible values:

```text
income
expense
```

#### By category

```http
GET /transactions?category=Food
```

#### By type and category

```http
GET /transactions?transaction_type=expense&category=Food
```

#### From a date

```http
GET /transactions?date_from=2026-09-01
```

#### Up to a date

```http
GET /transactions?date_to=2026-09-30
```

#### Date range

```http
GET /transactions?date_from=2026-09-01&date_to=2026-09-30
```

The filters can also be combined.

---

### Get One Transaction

```http
GET /transactions/{transaction_id}
```

Example:

```http
GET /transactions/1
```

Returns a single transaction belonging to the authenticated user.

If the transaction does not exist or does not belong to the user:

```text
404 Not Found
```

---

### Update Transaction

```http
PUT /transactions/{transaction_id}
```

Example:

```json
{
  "amount": 300,
  "category": "Food",
  "description": "Updated dinner",
  "transaction_type": "expense",
  "transaction_date": "2026-09-20"
}
```

Returns the updated transaction.

---

### Delete Transaction

```http
DELETE /transactions/{transaction_id}
```

Example:

```http
DELETE /transactions/1
```

Example response:

```json
{
  "message": "Transaction deleted successfully"
}
```

---

## Financial Summary

### Get Transaction Summary

```http
GET /transactions/summary
```

Returns a financial summary for the authenticated user.

Example response:

```json
{
  "total_income": 3000.0,
  "total_expenses": 700.0,
  "balance": 2300.0,
  "transaction_count": 3
}
```

The balance is calculated as:

```text
balance = total_income - total_expenses
```

The summary is calculated directly from the authenticated user's transactions.

For a user with no transactions:

```json
{
  "total_income": 0.0,
  "total_expenses": 0.0,
  "balance": 0.0,
  "transaction_count": 0
}
```

## Validation

The API uses Pydantic models to validate incoming data.

### Transaction amount

The amount must be greater than zero.

### Transaction type

Only:

```text
income
expense
```

are accepted.

### Transaction date

The date must be provided in a valid date format.

Example:

```text
2026-09-19
```

### Username

Username length must be between 3 and 50 characters.

### Password

Password length must be between 8 and 128 characters.

### Category

Category must contain between 1 and 50 characters.

### Description

Description must contain between 1 and 200 characters.

Invalid input is automatically rejected by FastAPI/Pydantic with a validation response.

## Database

The project uses **SQLite** for persistent data storage.

Two main tables are used:

### Users

```text
users
├── id
├── username
└── hashed_password
```

### Transactions

```text
transactions
├── id
├── user_id
├── amount
├── category
├── description
├── transaction_type
└── transaction_date
```

Each transaction contains a `user_id` foreign key connecting it to its owner.

SQLite foreign-key enforcement is enabled by the application.

## Financial Summary SQL

The financial summary is calculated using SQL aggregation instead of loading every transaction into Python.

The database calculates:

* Total income
* Total expenses
* Transaction count

Python then calculates:

```text
balance = total_income - total_expenses
```

This keeps data aggregation close to the database layer.

## Dependency Injection

FastAPI dependency injection is used for reusable components.

For example:

```python
Depends(get_db)
```

provides a database connection for an endpoint.

The current authenticated user is also provided through:

```python
Depends(get_current_user)
```

Database connections are automatically closed after the request finishes.

## Testing

The project uses **pytest** and FastAPI's testing tools.

The test suite currently contains:

```text
28 tests
```

The tests cover:

* Root endpoint
* User registration
* Duplicate usernames
* Password validation
* Login
* Incorrect passwords
* Authentication requirements
* Transaction validation
* Creating transactions
* Retrieving transactions
* Updating transactions
* Deleting transactions
* Transaction type filtering
* Category filtering
* Combined filtering
* Date filtering
* Transaction ownership
* Financial summary
* Empty financial summaries
* Summary authentication
* Summary user isolation

Run all tests with:

```powershell
python -m pytest
```

Current result:

```text
28 passed
```

Two dependency deprecation warnings may appear from FastAPI/Starlette/AnyIO's testing dependencies. They do not represent failures in the application tests.

## Running the Project

### 1. Activate the virtual environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Start the API

```powershell
python -m uvicorn main:app --reload
```

### 3. Open the API documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

FastAPI also provides OpenAPI documentation automatically.

## Environment Variables

Sensitive configuration is stored in `.env`.

Example:

```env
SECRET_KEY=your-secret-key
```

The `.env` file should not be committed to Git.

It is included in `.gitignore`.

## Git

The project is managed using Git and hosted on GitHub.

Repository:

```text
https://github.com/tahaamro298-sketch/finance-api
```

Typical workflow:

```powershell
git status
git add .
git commit -m "Add financial summary"
git push origin main
```

## API Development Flow

A typical request follows this pattern:

```text
Client
  ↓
FastAPI route
  ↓
Authentication / dependencies
  ↓
Pydantic validation
  ↓
Service layer
  ↓
Database layer
  ↓
SQLite
  ↓
Service layer
  ↓
API response
```

For example, a summary request:

```text
GET /transactions/summary
        ↓
Verify JWT
        ↓
Identify current user
        ↓
Call summary service
        ↓
Run SQL aggregation
        ↓
Calculate balance
        ↓
Return Summary response
```

## Future Improvements

Possible future features include:

* Category spending summaries
* Monthly financial reports
* Date-range summaries
* Budget management
* Recurring transactions
* Pagination
* More advanced search
* PostgreSQL support
* Docker deployment
* Production deployment
* API rate limiting
* Logging and monitoring
* CI/CD with GitHub Actions
* Frontend dashboard

## Learning Goals

This project is designed as a practical backend portfolio project and focuses on learning how to build and maintain a real API.

The project has covered:

* Python backend development
* REST APIs
* FastAPI
* HTTP methods
* Pydantic validation
* SQLite and SQL
* CRUD operations
* Authentication
* Password hashing
* JWT
* Authorization
* Dependency injection
* Service-layer architecture
* Automated testing
* Git and GitHub
* SQL aggregation
* Financial data processing

## Author

**Amro Taha**

Built as a practical backend development and portfolio project.
