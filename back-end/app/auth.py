"""Provider-neutral authentication boundary."""

from dataclasses import dataclass
from typing import Protocol


class AuthenticationFailed(Exception):
    """Raised when a supplied credential cannot be verified."""


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
        """Return the verified identity or raise AuthenticationFailed."""
