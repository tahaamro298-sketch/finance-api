# Finance API

A RESTful finance management API built with FastAPI, SQLite, JWT authentication, and automated testing.

## Features

- User registration
- Secure password hashing with Argon2
- User login with JWT access tokens
- Protected transaction endpoints
- User-specific transaction ownership
- Full transaction CRUD
- Request validation with Pydantic
- SQLite database
- Dependency injection
- Automated API tests with pytest
- Service-layer architecture

## Tech Stack

- Python
- FastAPI
- SQLite
- Pydantic
- PyJWT
- pwdlib with Argon2
- pytest
- Uvicorn

## Project Structure

```text
finance-api/
├── auth.py
├── database.py
├── dependencies.py
├── models.py
├── services.py
├── main.py
├── README.md
├── .gitignore
└── tests/
    └── test_main.py