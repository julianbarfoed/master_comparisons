"""Track metadata and its provider-neutral read boundary."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Track:
    """Persisted metadata for one owned audio track."""

    id: str
    owner_id: str
    title: str
    duration_seconds: float
    created_at: datetime


class TrackReader(Protocol):
    """Read the tracks visible to one verified user."""

    def list_tracks(self, user_id: str) -> list[Track]: ...


class TrackRepositoryUnavailable(RuntimeError):
    """Raised when track metadata cannot currently be read."""


class InMemoryTrackReader:
    """Owner-scoped reader used when composing routes in isolation."""

    def __init__(self, tracks: list[Track] | None = None) -> None:
        self._tracks = list(tracks or [])

    def list_tracks(self, user_id: str) -> list[Track]:
        return sorted(
            (track for track in self._tracks if track.owner_id == user_id),
            key=lambda track: (track.created_at, track.id),
            reverse=True,
        )
