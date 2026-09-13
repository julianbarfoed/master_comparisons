"""Provider-neutral authentication boundary and Supabase JWT verifier."""

from dataclasses import dataclass
from typing import Protocol

import jwt
from jwt import PyJWK, PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError, PyJWTError

SUPPORTED_SIGNING_ALGORITHMS = ("RS256", "ES256")


class AuthenticationFailed(Exception):
    """Raised when a supplied credential cannot be verified."""


class AuthenticationServiceUnavailable(Exception):
    """Raised when identity verification cannot reach its signing keys."""


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    """Identity established by a successful credential verification."""

    subject: str

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("identity subject must not be blank")


class IdentityVerifier(Protocol):
    """Verify opaque access tokens without exposing provider details."""

    def verify(self, token: str, /) -> VerifiedIdentity:
        """Return an identity or raise a typed credential/service failure."""


class _SigningKeyProvider(Protocol):
    def get_signing_key_from_jwt(self, token: str | bytes) -> PyJWK:
        """Return the cached or remotely discovered key for a JWT."""


class SupabaseIdentityVerifier:
    """Verify Supabase access tokens against the project's asymmetric signing keys."""

    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks_url: str,
        signing_key_provider: _SigningKeyProvider | None = None,
    ) -> None:
        """Configure issuer/audience checks and a cooldown-aware JWKS client."""
        self._issuer = issuer
        self._audience = audience
        self._signing_key_provider = signing_key_provider or PyJWKClient(
            jwks_url,
            cache_keys=False,
            cache_jwk_set=True,
            lifespan=600,
            timeout=5,
        )

    def verify(self, token: str, /) -> VerifiedIdentity:
        """Validate signature and required claims, then return the token subject."""
        try:
            header = jwt.get_unverified_header(token)
        except (InvalidTokenError, TypeError) as error:
            raise AuthenticationFailed from error

        key_id = header.get("kid")
        algorithm = header.get("alg")
        if not isinstance(key_id, str) or algorithm not in SUPPORTED_SIGNING_ALGORITHMS:
            raise AuthenticationFailed

        signing_key = self._resolve_signing_key(token, key_id, algorithm)

        try:
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=list(SUPPORTED_SIGNING_ALGORITHMS),
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except InvalidTokenError as error:
            raise AuthenticationFailed from error

        subject = claims.get("sub")
        if not isinstance(subject, str):
            raise AuthenticationFailed

        try:
            return VerifiedIdentity(subject=subject)
        except ValueError as error:
            raise AuthenticationFailed from error

    def _resolve_signing_key(self, token: str, key_id: str, algorithm: str) -> PyJWK:
        """Resolve the token key and classify credential versus provider failures."""
        try:
            signing_key = self._signing_key_provider.get_signing_key_from_jwt(token)
        except PyJWKClientError as error:
            # PyJWT uses one client exception for an unknown ``kid`` and for
            # malformed/empty JWKS responses. Its own message is the only
            # distinction available; unknown credentials are 401, while the
            # provider failures must surface as 503.
            if str(error).startswith("Unable to find a signing key that matches"):
                raise AuthenticationFailed from error
            raise AuthenticationServiceUnavailable from error
        except (PyJWTError, ValueError) as error:
            raise AuthenticationServiceUnavailable from error

        if signing_key.key_id != key_id or signing_key.algorithm_name != algorithm:
            raise AuthenticationFailed
        return signing_key
