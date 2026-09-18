from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from database import get_connection, get_user_by_id
from auth import decode_access_token


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