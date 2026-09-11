from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes.tracks import get_current_user_id, get_track_reader
from app.tracks import Track, TrackRepositoryUnavailable


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


class StubTrackReader:
    def __init__(self, tracks: list[Track]) -> None:
        self.tracks = tracks
        self.requested_user_id: str | None = None

    def list_tracks(self, user_id: str) -> list[Track]:
        self.requested_user_id = user_id
        return self.tracks


def authenticate_as(user_id: str) -> None:
    app.dependency_overrides[get_current_user_id] = lambda: user_id


def use_track_reader(reader: StubTrackReader) -> None:
    app.dependency_overrides[get_track_reader] = lambda: reader


def test_lists_tracks_for_authenticated_user():
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
    reader = StubTrackReader([])
    authenticate_as("user-1")
    use_track_reader(reader)

    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 200
    assert response.json() == []


def test_rejects_unauthenticated_request():
    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_maps_repository_unavailability_to_service_unavailable():
    class UnavailableTrackReader:
        def list_tracks(self, user_id: str) -> list[Track]:
            raise TrackRepositoryUnavailable

    authenticate_as("user-1")
    app.dependency_overrides[get_track_reader] = UnavailableTrackReader

    with TestClient(app) as client:
        response = client.get("/tracks")

    assert response.status_code == 503
    assert response.json() == {"detail": "Track library unavailable"}
