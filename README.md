# Finance API

[![CI](https://github.com/tahaamro298-sketch/finance-api/actions/workflows/ci.yml/badge.svg)](https://github.com/tahaamro298-sketch/finance-api/actions/workflows/ci.yml)

A production-style finance management REST API built with **Python, FastAPI, PostgreSQL, Docker, Docker Compose, JWT authentication, Argon2 password hashing, Pydantic, and pytest**.

The API allows users to register and authenticate securely, manage their own financial transactions, filter and paginate transaction data, and generate financial reports and summaries.

The project is designed as a practical backend portfolio project demonstrating API development, database design, authentication, testing, containerization, configuration management, deployment, and security practices.

## Live Demo

The Finance API is publicly deployed and accessible through Render.

### API

https://finance-api-amro.onrender.com

### Swagger UI

https://finance-api-amro.onrender.com/docs

### ReDoc

https://finance-api-amro.onrender.com/redoc

The deployed API uses:

* FastAPI
* Docker
* PostgreSQL
* JWT authentication
* HTTPS
* Render

---

## Current Status

* FastAPI REST API
* PostgreSQL database
* Docker + Docker Compose
* JWT authentication
* Argon2 password hashing
* User-specific authorization
* CRUD operations
* Filtering and pagination
* Financial summaries and reports
* Database migrations
* Centralized configuration
* CORS protection
* Trusted Host protection
* HTTP security headers
* Automated configuration and API tests
* Git/GitHub workflow
* Publicly deployed API
* HTTPS-enabled production environment
* Hosted PostgreSQL database

Current automated test suite:

```text
57 passed
2 dependency deprecation warnings
```

---

## Features

### Authentication and authorization

* User registration
* User login
* OAuth2 password-form authentication
* JWT Bearer tokens
* Argon2 password hashing
* Protected endpoints
* User-specific transaction ownership
* Users can only access their own transactions

### Transaction management

* Create transactions
* Retrieve all transactions
* Retrieve one transaction
* Update transactions
* Delete transactions
* Income and expense transaction types
* Transaction dates
* Category and description fields

### Filtering and pagination

Transactions can be filtered by:

* Transaction type
* Category
* Start date
* End date
* Combined filters

Pagination supports:

* `limit`
* `offset`
* Total matching transaction count

### Financial reports

* Total income
* Total expenses
* Balance
* Transaction count
* Category expense summaries
* Monthly financial summaries
* Date-range reports

### Validation and error handling

* Pydantic request validation
* Standardized API error responses
* HTTP error handling
* Validation error handling
* Date-range validation
* Safe resource ownership checks

### Security

* Argon2 password hashing
* JWT authentication
* Environment-based secrets
* Production configuration validation
* Explicit CORS origins
* Trusted Host validation
* Security response headers
* Sensitive `.env` file excluded from Git
* Runtime and development dependencies separated

### Testing

The project includes automated tests for:

* Authentication
* Registration
* Login
* Authorization
* CRUD operations
* Ownership isolation
* Validation
* Filtering
* Pagination
* Financial summaries
* Category summaries
* Monthly summaries
* Error responses
* CORS configuration
* Security headers
* Trusted Host protection
* Production configuration rules
* Database migrations

---

## Technology Stack

### Backend

* Python 3.14
* FastAPI
* Uvicorn
* Pydantic
* Psycopg 3
* PostgreSQL 18
* pwdlib
* Argon2
* PyJWT
* python-dotenv
* python-multipart

### Testing

* pytest
* HTTPX

### Infrastructure

* Docker
* Docker Compose
* Render
* PostgreSQL

### Version control

* Git
* GitHub

---

## Architecture

The application uses a layered architecture:

```text
Client
   |
   v
main.py
   |
   v
dependencies.py
   |
   +------> Authentication / Current User
   |
   v
services.py
   |
   v
database.py
   |
   v
PostgreSQL
```

Supporting components:

```text
models.py
    |
    +--> Request validation
    +--> Response models

auth.py
    |
    +--> Argon2 password hashing
    +--> JWT creation and decoding

config.py
    |
    +--> Environment configuration
    +--> Production validation

migrations.py
    |
    +--> Database schema migrations

tests/
    |
    +--> Automated regression tests
```

### Request flow

A typical authenticated request follows:

```text
HTTP Request
     |
     v
Trusted Host validation
     |
     v
CORS middleware
     |
     v
Security headers middleware
     |
     v
FastAPI route
     |
     v
Authentication / dependencies
     |
     v
Pydantic validation
     |
     v
Service layer
     |
     v
Database layer
     |
     v
PostgreSQL
     |
     v
API response
```

---

## Project Structure

```text
finance-api/
|
+-- main.py
+-- models.py
+-- database.py
+-- services.py
+-- dependencies.py
+-- auth.py
+-- migrations.py
+-- config.py
|
+-- Dockerfile
+-- compose.yml
+-- .dockerignore
+-- requirements.txt
+-- requirements-dev.txt
+-- .env.example
+-- .gitignore
+-- README.md
|
+-- tests/
    +-- test_main.py
    +-- test_migrations.py
    +-- test_config.py
```

### File responsibilities

**`main.py`**

Contains the FastAPI application, routes, middleware, and HTTP error handlers.

**`models.py`**

Contains Pydantic request and response models.

**`services.py`**

Contains application and business logic between HTTP routes and the database layer.

**`database.py`**

Contains PostgreSQL connections and database queries.

**`auth.py`**

Contains password hashing, JWT creation, and JWT decoding.

**`dependencies.py`**

Contains reusable FastAPI dependencies such as database connections and the current authenticated user.

**`config.py`**

Loads environment configuration and validates security-sensitive production settings.

**`migrations.py`**

Manages database schema versioning and migrations.

**`tests/test_main.py`**

Contains API-level tests.

**`tests/test_migrations.py`**

Tests database migrations and schema upgrades.

**`tests/test_config.py`**

Tests production configuration validation.

---

# Authentication

The API uses:

* **Argon2** for password hashing
* **JWT Bearer tokens** for authentication
* **OAuth2 password-form login**

Passwords are never stored in plain text.

### Registration

```http
POST /register
```

Example:

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

Response:

```text
201 Created
```

### Login

```http
POST /login
```

The endpoint accepts OAuth2 password-form data:

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

Protected requests use:

```text
Authorization: Bearer <token>
```

JWT tokens expire after a configured period.

---

# Transactions API

All transaction endpoints require authentication.

## Create transaction

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

Response:

```text
201 Created
```

## Get transactions

```http
GET /transactions
```

Returns transactions belonging only to the authenticated user.

Transactions are ordered by newest transaction date first.

### Pagination

```http
GET /transactions?limit=20&offset=0
```

Example response:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

### Filter by transaction type

```http
GET /transactions?transaction_type=expense
```

Accepted values:

```text
income
expense
```

### Filter by category

```http
GET /transactions?category=Food
```

### Filter by date

```http
GET /transactions?date_from=2026-09-01
```

```http
GET /transactions?date_to=2026-09-30
```

### Filter by date range

```http
GET /transactions?date_from=2026-09-01&date_to=2026-09-30
```

Filters can be combined with pagination.

## Get one transaction

```http
GET /transactions/{transaction_id}
```

Example:

```http
GET /transactions/1
```

The endpoint returns the transaction only if it belongs to the authenticated user.

Otherwise:

```text
404 Not Found
```

## Update transaction

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

## Delete transaction

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

# Financial Reports

## Transaction summary

```http
GET /transactions/summary
```

Returns:

* Total income
* Total expenses
* Balance
* Transaction count

Example:

```json
{
  "total_income": 3000.0,
  "total_expenses": 700.0,
  "balance": 2300.0,
  "transaction_count": 3
}
```

The balance is:

```text
balance = total_income - total_expenses
```

The report can optionally be restricted to a date range:

```http
GET /transactions/summary?date_from=2026-09-01&date_to=2026-09-30
```

## Category summary

```http
GET /transactions/category-summary
```

Provides expense totals grouped by category.

Optional date filters are supported.

## Monthly summary

```http
GET /transactions/monthly-summary
```

Provides monthly income and expense totals.

Optional date filters are supported.

---

# Validation

The API uses Pydantic models for request validation.

Important validation rules include:

* Username: 3–50 characters
* Password: 8–128 characters
* Category: 1–50 characters
* Description: 1–200 characters
* Amount: greater than zero
* Transaction type: `income` or `expense`
* Transaction date: valid date
* `date_from` cannot be after `date_to`
* Pagination values must be within their configured limits

Invalid requests return a standardized validation response.

Example:

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": []
}
```

---

# Error Handling

The API uses standardized error responses.

Examples include:

```text
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
405 Method Not Allowed
422 Validation Error
```

Example:

```json
{
  "error": "not_found",
  "message": "Transaction not found"
}
```

This keeps error responses predictable for frontend clients and other API consumers.

---

# Database

The application uses **PostgreSQL 18**.

Main tables:

## Users

```text
users
+-- id
+-- username
+-- hashed_password
```

## Transactions

```text
transactions
+-- id
+-- user_id
+-- amount
+-- category
+-- description
+-- transaction_type
+-- transaction_date
```

Each transaction belongs to a user through `user_id`.

Database schema changes are managed using the migration system in `migrations.py`.

The project also maintains a separate PostgreSQL database for automated tests.

```text
Application database
    finance

Test database
    finance_test
```

This prevents the automated tests from modifying the normal application database.

---

# Docker

The project runs as a multi-container backend using Docker Compose.

Architecture:

```text
Docker Compose
|
+-- api
|   +-- FastAPI
|   +-- Uvicorn
|
+-- db
    +-- PostgreSQL 18
```

A persistent Docker volume is used for PostgreSQL data:

```text
postgres_data
```

This allows database data to survive container recreation.

---

# Deployment

The API is deployed using **Render** and uses the same Dockerfile used for local development.

### Deployment architecture

```text
GitHub
   |
   v
Render Web Service
   |
   +----------------------+
   |                      |
   v                      v
Docker Container      Render PostgreSQL
   |
   v
FastAPI
```

### Production request flow

```text
Internet
   |
   v
HTTPS
   |
   v
Render
   |
   v
FastAPI
   |
   +--> JWT Authentication
   |
   +--> Business Logic
   |
   v
PostgreSQL
```

### Production configuration

The deployed application uses environment variables for:

* Application environment
* CORS origins
* Allowed hosts
* JWT secret
* PostgreSQL host
* PostgreSQL port
* PostgreSQL database
* PostgreSQL user
* PostgreSQL password
* Render-provided service port

Sensitive configuration is not stored in the Git repository.

### Production verification

The deployment was verified by:

* Opening the live API
* Opening Swagger UI
* Registering a user
* Logging in
* Authenticating with JWT
* Creating a transaction
* Retrieving transactions
* Retrieving the financial summary
* Connecting successfully to hosted PostgreSQL

New commits to the `main` branch can trigger automatic Render deployments.

---

# Quick Start

The recommended way to run the project locally is with Docker Compose.

## Prerequisites

Install:

* Docker Desktop
* Git

Verify Docker:

```powershell
docker --version
docker compose version
```

## 1. Clone the repository

```powershell
git clone https://github.com/tahaamro298-sketch/finance-api.git
cd finance-api
```

## 2. Create the environment file

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace the placeholder values with your own secrets and local configuration.

Do not commit `.env`.

## 3. Start the application

```powershell
docker compose up --build -d
```

Check the containers:

```powershell
docker compose ps
```

The database should show:

```text
healthy
```

and the API should show:

```text
Up
```

## 4. Open the API

API:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

## 5. Run the tests

From the project environment:

```powershell
python -m pytest
```

Expected result:

```text
57 passed
```

## 6. View logs

API logs:

```powershell
docker compose logs api
```

Database logs:

```powershell
docker compose logs db
```

Follow API logs live:

```powershell
docker compose logs -f api
```

## 7. Stop the application

```powershell
docker compose down
```

This stops the containers while keeping the PostgreSQL volume.

To remove the PostgreSQL volume and its stored data:

```powershell
docker compose down -v
```

Use the `-v` option only when you intentionally want to reset the database.

---

# Local Development

Docker is the recommended reproducible environment.

For development without Docker, activate the Python virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Make sure `.env` points to a locally running PostgreSQL instance.

Start FastAPI:

```powershell
python -m uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

---

# API Documentation

FastAPI automatically generates OpenAPI documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Production Swagger UI:

```text
https://finance-api-amro.onrender.com/docs
```

Alternative ReDoc documentation:

```text
http://127.0.0.1:8000/redoc
```

Production ReDoc:

```text
https://finance-api-amro.onrender.com/redoc
```

The generated documentation allows developers to inspect and test the API interactively.

---

# API Endpoint Map

| Method   | Endpoint                         | Authentication | Purpose                                 |
| -------- | -------------------------------- | -------------- | --------------------------------------- |
| `GET`    | `/`                              | No             | Health/basic response                   |
| `POST`   | `/register`                      | No             | Create a user account                   |
| `POST`   | `/login`                         | No             | Authenticate and receive JWT            |
| `POST`   | `/transactions`                  | Yes            | Create a transaction                    |
| `GET`    | `/transactions`                  | Yes            | List, filter, and paginate transactions |
| `GET`    | `/transactions/{transaction_id}` | Yes            | Retrieve one owned transaction          |
| `PUT`    | `/transactions/{transaction_id}` | Yes            | Update an owned transaction             |
| `DELETE` | `/transactions/{transaction_id}` | Yes            | Delete an owned transaction             |
| `GET`    | `/transactions/summary`          | Yes            | Financial summary                       |
| `GET`    | `/transactions/category-summary` | Yes            | Expense totals by category              |
| `GET`    | `/transactions/monthly-summary`  | Yes            | Monthly income/expense report           |

---

# Architecture at a Glance

```text
                    +-----------------+
                    |     Client      |
                    +--------+--------+
                             |
                             v
                    +-----------------+
                    |    FastAPI      |
                    |    main.py      |
                    +--------+--------+
                             |
                    +--------v--------+
                    |  Dependencies   |
                    | Auth / Database |
                    +--------+--------+
                             |
                    +--------v--------+
                    |    Services     |
                    | Business Logic  |
                    +--------+--------+
                             |
                    +--------v--------+
                    |    Database     |
                    |  PostgreSQL 18  |
                    +--------+--------+
                             |
                    +--------v--------+
                    | Docker / Render |
                    +-----------------+

Supporting systems:

- config.py       -> Environment and production configuration
- auth.py         -> Argon2 + JWT
- migrations.py   -> Schema migrations
- tests/          -> Automated regression tests
```

---

# Configuration

The project uses environment variables for configuration.

Example:

```env
APP_ENV=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
ALLOWED_HOSTS=localhost,127.0.0.1

SECRET_KEY=replace_with_a_secure_secret

DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=finance
DATABASE_USER=finance_app
DATABASE_PASSWORD=replace_with_database_password
```

The repository includes:

```text
.env.example
```

but the real:

```text
.env
```

must remain private.

### Production configuration

When:

```env
APP_ENV=production
```

the application performs additional validation.

Production configuration must include:

* A sufficiently strong `SECRET_KEY`
* Explicit `ALLOWED_HOSTS`
* Explicit `CORS_ORIGINS`
* No wildcard `*` CORS configuration

The application is designed to fail fast when security-sensitive production configuration is invalid.

When running on Render, the application also reads Render's service hostname automatically for trusted-host validation.

---

# Security

The project includes several production-oriented protections.

### Authentication

* Argon2 password hashing
* JWT authentication
* User-specific authorization

### Browser/API security

* Explicit CORS origins
* Trusted Host validation
* `X-Content-Type-Options: nosniff`
* `X-Frame-Options: DENY`
* `Referrer-Policy: no-referrer`
* `Permissions-Policy`

### Secret management

* Secrets stored in environment variables
* `.env` excluded from Git
* `.env.example` contains placeholders only
* Production configuration validation
* Render environment variables used for deployed secrets

### Database security

The application uses a dedicated PostgreSQL role rather than relying on the PostgreSQL installation's administrative account.

---

# Testing

The project uses pytest for automated testing.

Run the full suite:

```powershell
python -m pytest
```

Current test result:

```text
57 passed
2 dependency deprecation warnings
```

The test suite covers:

* Root endpoint
* Registration
* Login
* Password validation
* Authentication
* Authorization
* CRUD
* Ownership isolation
* Filtering
* Pagination
* Financial summaries
* Category summaries
* Monthly summaries
* Date validation
* Error response formats
* Security headers
* CORS behavior
* Trusted Host behavior
* Production configuration
* Database migrations

The project uses a dedicated test database:

```text
finance_test
```

so tests are isolated from the main application database.

---

# Development Workflow

Typical development workflow:

```powershell
git status
```

Make changes and run:

```powershell
python -m pytest
```

Check whitespace errors:

```powershell
git diff --check
```

Inspect changes:

```powershell
git diff
```

Commit:

```powershell
git add .
git commit -m "Describe the change"
```

Push:

```powershell
git push
```

The project is maintained using Git and hosted on GitHub.

Repository:

```text
https://github.com/tahaamro298-sketch/finance-api
```

---

# Project Development Progress

The project was built incrementally.

Major milestones include:

```text
FastAPI foundation
      |
      v
CRUD
      |
      v
Persistent database
      |
      v
Authentication
      |
      v
Authorization
      |
      v
Service-layer architecture
      |
      v
Financial reports
      |
      v
Pagination and filtering
      |
      v
Standardized errors
      |
      v
Database migrations
      |
      v
PostgreSQL
      |
      v
Docker
      |
      v
Production configuration
      |
      v
Security hardening
      |
      v
Automated regression tests
      |
      v
API documentation
      |
      v
Public deployment
```

---

# Future Development

Planned next stages include:

* CI/CD with GitHub Actions
* Frontend application
* API/frontend integration
* Financial dashboard
* Charts and visual reporting
* Responsive UI
* Final portfolio polish
* Production monitoring improvements
* More advanced deployment infrastructure

---

# Learning Goals

This project was built as a practical backend portfolio project.

The main skills demonstrated are:

* Python backend development
* REST API design
* FastAPI
* Pydantic validation
* PostgreSQL and SQL
* CRUD operations
* Authentication and authorization
* JWT
* Argon2
* Dependency injection
* Service-layer architecture
* Database migrations
* Pagination and filtering
* SQL aggregation
* Automated testing
* Git and GitHub
* Docker
* Docker Compose
* Render deployment
* Environment-based configuration
* API security
* Production-oriented development

---

# Author

**Amro Taha**

This project was built as a practical backend development and portfolio project.
