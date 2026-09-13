"""Tests for Supabase and browser-origin configuration."""

import pytest

from app.config import AuthConfigurationError, AuthSettings, get_web_origin


def test_web_origin_defaults_to_the_local_frontend():
    """Use the documented Vite origin when no override is supplied."""
    assert get_web_origin({}) == "http://localhost:5173"


def test_web_origin_rejects_a_path():
    """Reject values that are URLs rather than browser origins."""
    with pytest.raises(AuthConfigurationError, match="must not contain a path"):
        get_web_origin({"WEB_ORIGIN": "http://localhost:5173/app"})


def test_auth_settings_derive_supabase_jwt_endpoints():
    """Derive the canonical Supabase issuer and JWKS endpoint."""
    settings = AuthSettings.from_env({"SUPABASE_URL": "https://project-ref.supabase.co/"})

    assert settings.jwt_issuer == "https://project-ref.supabase.co/auth/v1"
    assert settings.jwt_audience == "authenticated"
    assert settings.jwks_url == (
        "https://project-ref.supabase.co/auth/v1/.well-known/jwks.json"
    )


def test_auth_settings_require_a_supabase_url():
    """Require the project URL needed to build default auth endpoints."""
    with pytest.raises(AuthConfigurationError, match="SUPABASE_URL is required"):
        AuthSettings.from_env({})


def test_auth_settings_accept_explicit_jwt_overrides():
    """Honor explicit issuer, audience, and JWKS settings for custom deployments."""
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
