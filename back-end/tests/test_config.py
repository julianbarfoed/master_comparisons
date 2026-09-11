import pytest

from app.config import (
    AuthConfigurationError,
    AuthSettings,
    DatabaseConfigurationError,
    DatabaseSettings,
)


def test_database_settings_load_a_postgres_url():
    settings = DatabaseSettings.from_env(
        {"DATABASE_URL": "postgresql://audio-api:secret@db.example.test:5432/postgres"}
    )

    assert settings.database_url == (
        "postgresql://audio-api:secret@db.example.test:5432/postgres"
    )


@pytest.mark.parametrize("database_url", ["", "sqlite:///local.db", "postgresql:///missing-host"])
def test_database_settings_require_a_postgres_url(database_url: str):
    with pytest.raises(DatabaseConfigurationError):
        DatabaseSettings.from_env({"DATABASE_URL": database_url})


def test_auth_settings_derive_supabase_jwt_endpoints():
    settings = AuthSettings.from_env({"SUPABASE_URL": "https://project-ref.supabase.co/"})

    assert settings.jwt_issuer == "https://project-ref.supabase.co/auth/v1"
    assert settings.jwt_audience == "authenticated"
    assert settings.jwks_url == (
        "https://project-ref.supabase.co/auth/v1/.well-known/jwks.json"
    )


def test_auth_settings_require_a_supabase_url():
    with pytest.raises(AuthConfigurationError, match="SUPABASE_URL is required"):
        AuthSettings.from_env({})


def test_auth_settings_accept_explicit_jwt_overrides():
    settings = AuthSettings.from_env(
        {
            "SUPABASE_URL": "http://supabase.local",
            "SUPABASE_JWT_ISSUER": "http://auth.local/issuer",
            "SUPABASE_JWT_AUDIENCE": "audio-api",
            "SUPABASE_JWKS_URL": "http://keys.local/jwks.json",
        }
    )

    assert settings.jwt_issuer == "http://auth.local/issuer"
    assert settings.jwt_audience == "audio-api"
    assert settings.jwks_url == "http://keys.local/jwks.json"
