"""Reusable FastAPI dependencies shared by authenticated routes."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth import (
    AuthenticationFailed,
    AuthenticationServiceUnavailable,
    IdentityVerifier,
    SupabaseIdentityVerifier,
    VerifiedIdentity,
)
from app.config import AuthConfigurationError, AuthSettings

_bearer_scheme = HTTPBearer(auto_error=False)


class _UnavailableIdentityVerifier:
    def __init__(self, cause: AuthConfigurationError) -> None:
        self._cause = cause

    def verify(self, token: str, /) -> VerifiedIdentity:
        raise AuthenticationServiceUnavailable from self._cause


@lru_cache
def get_identity_verifier() -> IdentityVerifier:
    """Build one cached verifier from environment-backed Supabase settings."""
    try:
        settings = AuthSettings.from_env()
    except AuthConfigurationError as error:
        return _UnavailableIdentityVerifier(error)

    return SupabaseIdentityVerifier(
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
        jwks_url=settings.jwks_url,
    )


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    verifier: Annotated[IdentityVerifier, Depends(get_identity_verifier)],
) -> str:
    """Return the verified bearer-token subject for an authenticated request."""
    if credentials is None:
        raise _authentication_required()

    try:
        identity = verifier.verify(credentials.credentials)
    except AuthenticationFailed as error:
        raise _authentication_required() from error
    except AuthenticationServiceUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        ) from error

    return identity.subject


def _authentication_required() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
