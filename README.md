# Finance API
A RESTful API for managing personal financial transactions, built with FastAPI and SQLite.

## Features

- Create financial transactions
- View all transactions
- View a single transaction
- Update transactions
- Delete transactions
- Input validation
- Automated API testing
- SQLite database storage

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLite
- Pytest
- Uvicorn

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Check that the API is running |
| POST | `/transactions` | Create a transaction |
| GET | `/transactions` | Get all transactions |
| GET | `/transactions/{transaction_id}` | Get one transaction |
| PUT | `/transactions/{transaction_id}` | Update a transaction |
| DELETE | `/transactions/{transaction_id}` | Delete a transaction |

## Installation

Clone the repository:

```bash
git clone https://github.com/tahaamro298-sketch/finance-api.git
cd finance-api

Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate

Install the dependencies
pip install fastapi uvicorn pydantic pytest httpx

## Running the API

Start the development server:

```bash
python -m uvicorn main:app --reload

the API will be available at
http://127.0.0.1:8000

Interactive API documentation is available at:
http://127.0.0.1:8000/docs

## Testing

Run the automated test suite:

```bash
python -m pytest

## Project Structure

```text
finance-api/
├── main.py
├── database.py
├── tests/
│   └── test_main.py
├── .gitignore
└── README.md

## Author

Amro Taha