"""Provider-neutral track metadata boundary used by the HTTP API."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Track:
    """Metadata required by the first library response."""

    id: str
    title: str
    duration_seconds: float


class TrackReader(Protocol):
    """Read the tracks visible to one verified user."""

    def list_tracks(self, user_id: str) -> list[Track]: ...


class TrackRepositoryUnavailable(RuntimeError):
    """Raised when track metadata cannot currently be read."""
