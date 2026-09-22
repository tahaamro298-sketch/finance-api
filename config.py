import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_env: str
    cors_origins: list[str]
    allowed_hosts: list[str]
    secret_key: str
    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str


def load_settings():
    app_env = os.getenv(
        "APP_ENV",
        "development"
    )

    cors_origins_raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173"
    )

    cors_origins = [
        origin.strip()
        for origin in cors_origins_raw.split(",")
        if origin.strip()
    ]

    allowed_hosts_raw = os.getenv(
        "ALLOWED_HOSTS",
        "localhost,127.0.0.1"
    )

    allowed_hosts = [
        host.strip()
        for host in allowed_hosts_raw.split(",")
        if host.strip()
    ]

    # FastAPI TestClient uses "testserver".
    # Allow it automatically only in development.
    if (
        app_env == "development"
        and "testserver" not in allowed_hosts
    ):
        allowed_hosts.append("testserver")

    secret_key = os.getenv("SECRET_KEY")
    database_host = os.getenv("DATABASE_HOST")
    database_port = os.getenv("DATABASE_PORT")
    database_name = os.getenv("DATABASE_NAME")
    database_user = os.getenv("DATABASE_USER")
    database_password = os.getenv("DATABASE_PASSWORD")

    missing = []

    if not secret_key:
        missing.append("SECRET_KEY")

    if not database_host:
        missing.append("DATABASE_HOST")

    if not database_port:
        missing.append("DATABASE_PORT")

    if not database_name:
        missing.append("DATABASE_NAME")

    if not database_user:
        missing.append("DATABASE_USER")

    if not database_password:
        missing.append("DATABASE_PASSWORD")

    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
        )

    if app_env == "production":
        if len(secret_key) < 32:
            raise RuntimeError(
                "SECRET_KEY must contain at least 32 characters in production"
            )

        if not os.getenv("ALLOWED_HOSTS"):
            raise RuntimeError(
                "ALLOWED_HOSTS must be explicitly configured in production"
            )

        if not os.getenv("CORS_ORIGINS"):
            raise RuntimeError(
                "CORS_ORIGINS must be explicitly configured in production"
            )

        if "*" in cors_origins:
            raise RuntimeError(
                "CORS_ORIGINS cannot contain '*' in production"
            )

    try:
        database_port_value = int(database_port)
    except ValueError as exc:
        raise RuntimeError(
            "DATABASE_PORT must be a valid integer"
        ) from exc

    return Settings(
        app_env=app_env,
        cors_origins=cors_origins,
        allowed_hosts=allowed_hosts,
        secret_key=secret_key,
        database_host=database_host,
        database_port=database_port_value,
        database_name=database_name,
        database_user=database_user,
        database_password=database_password
    )


settings = load_settings()