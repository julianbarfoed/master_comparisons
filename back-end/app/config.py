"""Environment-backed application settings."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlparse


class AuthConfigurationError(RuntimeError):
    """Raised when authentication settings are missing or invalid."""


def get_web_origin(environ: Mapping[str, str] | None = None) -> str:
    """Return the browser origin allowed to call the API.

    ``WEB_ORIGIN`` is intentionally a single explicit origin so credentialed
    browser requests cannot be opened to arbitrary sites. The local frontend
    origin is the safe development default.
    """
    source = os.environ if environ is None else environ
    origin = source.get("WEB_ORIGIN", "http://localhost:5173").strip().rstrip("/")
    _validate_http_url("WEB_ORIGIN", origin)
    parsed = urlparse(origin)
    if parsed.path or parsed.query or parsed.fragment:
        raise AuthConfigurationError("WEB_ORIGIN must not contain a path or query")
    return origin


@dataclass(frozen=True, slots=True)
class AuthSettings:
    """Supabase values required to verify access tokens."""

    supabase_url: str
    jwt_issuer: str
    jwt_audience: str
    jwks_url: str

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "AuthSettings":
        """Load Supabase URL, issuer, audience, and JWKS settings from an environment mapping."""
        source = os.environ if environ is None else environ
        supabase_url = source.get("SUPABASE_URL", "").strip().rstrip("/")
        if not supabase_url:
            raise AuthConfigurationError("SUPABASE_URL is required")
        _validate_http_url("SUPABASE_URL", supabase_url)

        jwt_issuer = source.get("SUPABASE_JWT_ISSUER", "").strip().rstrip("/")
        if not jwt_issuer:
            jwt_issuer = f"{supabase_url}/auth/v1"
        _validate_http_url("SUPABASE_JWT_ISSUER", jwt_issuer)

        jwks_url = source.get("SUPABASE_JWKS_URL", "").strip()
        if not jwks_url:
            jwks_url = f"{jwt_issuer}/.well-known/jwks.json"
        _validate_http_url("SUPABASE_JWKS_URL", jwks_url)

        jwt_audience = source.get("SUPABASE_JWT_AUDIENCE", "authenticated").strip()
        if not jwt_audience:
            raise AuthConfigurationError("SUPABASE_JWT_AUDIENCE must not be blank")

        return cls(
            supabase_url=supabase_url,
            jwt_issuer=jwt_issuer,
            jwt_audience=jwt_audience,
            jwks_url=jwks_url,
        )


def _validate_http_url(name: str, value: str) -> None:
    """Reject missing URL schemes/hosts before they reach an HTTP client."""
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AuthConfigurationError(f"{name} must be an HTTP(S) URL")
