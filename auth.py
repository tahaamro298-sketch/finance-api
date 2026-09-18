import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash


load_dotenv()


SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not configured")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Use Argon2 for secure password hashing
password_hash = PasswordHash.recommended()


def hash_password(password):
    return password_hash.hash(password)


def verify_password(password, hashed_password):
    return password_hash.verify(password, hashed_password)


# Create a JWT access token containing the user's ID
def create_access_token(user_id):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# Decode a JWT and return the user ID stored in its "sub" claim
def decode_access_token(token):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except (jwt.PyJWTError, ValueError, TypeError):
        return None