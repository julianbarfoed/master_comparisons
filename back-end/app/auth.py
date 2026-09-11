"""Provider-neutral authentication boundary and Supabase JWT verifier."""

from dataclasses import dataclass
from typing import Protocol

import jwt
from jwt import PyJWK, PyJWKClient
from jwt.exceptions import InvalidTokenError, PyJWKClientError

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
    def get_signing_keys(self, refresh: bool = False) -> list[PyJWK]: ...


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

        signing_key = self._resolve_signing_key(key_id, algorithm)

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

    def _resolve_signing_key(self, key_id: str, algorithm: str) -> PyJWK:
        try:
            signing_keys = self._signing_key_provider.get_signing_keys()
            signing_key = self._matching_key(signing_keys, key_id, algorithm)
            if signing_key is None:
                signing_keys = self._signing_key_provider.get_signing_keys(refresh=True)
                signing_key = self._matching_key(signing_keys, key_id, algorithm)
        except PyJWKClientError as error:
            raise AuthenticationServiceUnavailable from error

        if signing_key is None:
            raise AuthenticationFailed
        return signing_key

    @staticmethod
    def _matching_key(signing_keys: list[PyJWK], key_id: str, algorithm: str) -> PyJWK | None:
        return next(
            (
                key
                for key in signing_keys
                if key.key_id == key_id and key.algorithm_name == algorithm
            ),
            None,
        )
