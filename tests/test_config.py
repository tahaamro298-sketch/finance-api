import pytest

from config import load_settings


def set_base_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv(
        "SECRET_KEY",
        "a" * 64
    )
    monkeypatch.setenv(
        "DATABASE_HOST",
        "localhost"
    )
    monkeypatch.setenv(
        "DATABASE_PORT",
        "5432"
    )
    monkeypatch.setenv(
        "DATABASE_NAME",
        "finance"
    )
    monkeypatch.setenv(
        "DATABASE_USER",
        "finance_app"
    )
    monkeypatch.setenv(
        "DATABASE_PASSWORD",
        "test-password"
    )


def test_production_configuration_loads(monkeypatch):
    set_base_environment(monkeypatch)

    monkeypatch.setenv(
        "ALLOWED_HOSTS",
        "api.example.com"
    )

    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.example.com"
    )

    settings = load_settings()

    assert settings.app_env == "production"
    assert settings.allowed_hosts == ["api.example.com"]
    assert settings.cors_origins == [
        "https://app.example.com"
    ]
    assert settings.database_port == 5432


def test_production_requires_strong_secret(monkeypatch):
    set_base_environment(monkeypatch)

    monkeypatch.setenv(
        "SECRET_KEY",
        "too-short"
    )

    monkeypatch.setenv(
        "ALLOWED_HOSTS",
        "api.example.com"
    )

    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.example.com"
    )

    with pytest.raises(
        RuntimeError,
        match="SECRET_KEY must contain at least 32 characters"
    ):
        load_settings()


def test_production_requires_allowed_hosts(monkeypatch):
    set_base_environment(monkeypatch)

    monkeypatch.delenv(
        "ALLOWED_HOSTS",
        raising=False
    )

    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.example.com"
    )

    with pytest.raises(
        RuntimeError,
        match="ALLOWED_HOSTS must be explicitly configured"
    ):
        load_settings()


def test_production_requires_cors_origins(monkeypatch):
    set_base_environment(monkeypatch)

    monkeypatch.setenv(
        "ALLOWED_HOSTS",
        "api.example.com"
    )

    monkeypatch.delenv(
        "CORS_ORIGINS",
        raising=False
    )

    with pytest.raises(
        RuntimeError,
        match="CORS_ORIGINS must be explicitly configured"
    ):
        load_settings()


def test_production_rejects_wildcard_cors(monkeypatch):
    set_base_environment(monkeypatch)

    monkeypatch.setenv(
        "ALLOWED_HOSTS",
        "api.example.com"
    )

    monkeypatch.setenv(
        "CORS_ORIGINS",
        "*"
    )

    with pytest.raises(
        RuntimeError,
        match="CORS_ORIGINS cannot contain '\\*'"
    ):
        load_settings()