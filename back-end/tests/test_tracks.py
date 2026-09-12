"""HTTP contract tests for the authenticated track route."""

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_current_user_id
from app.main import app
from app.routes.tracks import get_track_reader
from app.tracks import Track, TrackRepositoryUnavailable


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Iterator[None]:
    """Remove test dependency replacements after each route test."""
    yield
    app.dependency_overrides.clear()


class StubTrackReader:
    """Record which verified owner the route passes to a fake reader."""

    def __init__(self, tracks: list[Track]) -> None:
        """Initialize the fake reader with the rows it should return."""
        self.tracks = tracks
        self.requested_user_id: str | None = None

    def list_tracks(self, user_id: str) -> list[Track]:
        """Capture the owner and return the configured track rows."""
        self.requested_user_id = user_id
        return self.tracks


def authenticate_as(user_id: str) -> None:
    """Override M1-A identity resolution with a deterministic verified subject."""
    app.dependency_overrides[get_current_user_id] = lambda: user_id


def use_track_reader(reader: StubTrackReader) -> None:
    """Override database access with a supplied reader double."""
    app.dependency_overrides[get_track_reader] = lambda: reader


def test_lists_tracks_for_authenticated_user():
    """The route exposes only the documented track summary fields."""
    reader = StubTrackReader(
        [
            Track(
                id="track-1",
                owner_id="user-1",
                title="First recording",
                duration_seconds=12.5,
                created_at=datetime(2026, 9, 11, tzinfo=UTC),
            )
        ]
    )
    authenticate_as("user-1")
    use_track_reader(reader)

    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "track-1", "title": "First recording", "duration_seconds": 12.5}
    ]
    assert reader.requested_user_id == "user-1"


def test_lists_an_empty_library():
    """An authenticated owner with no rows receives an empty JSON array."""
    reader = StubTrackReader([])
    authenticate_as("user-1")
    use_track_reader(reader)

    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 200
    assert response.json() == []


def test_rejects_unauthenticated_request():
    """Missing bearer credentials are rejected by the auth dependency."""
    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_maps_repository_unavailability_to_service_unavailable():
    """Reader outages are returned as the stable 503 API error."""

    class UnavailableTrackReader:
        """Reader double that simulates a database dependency outage."""

        def list_tracks(self, user_id: str) -> list[Track]:
            """Raise the repository failure expected from an unavailable database."""
            raise TrackRepositoryUnavailable

    authenticate_as("user-1")
    app.dependency_overrides[get_track_reader] = UnavailableTrackReader

    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 503
    assert response.json() == {"detail": "Track library unavailable"}


def test_maps_missing_database_configuration_to_service_unavailable(monkeypatch):
    """Missing backend database configuration is reported as dependency failure."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    authenticate_as("user-1")

    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 503
    assert response.json() == {"detail": "Track library unavailable"}
