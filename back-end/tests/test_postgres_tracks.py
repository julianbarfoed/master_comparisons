"""Integration tests for the Postgres-backed track library."""

from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.auth import VerifiedIdentity
from app.db import PostgresTrackRepository
from app.dependencies import get_identity_verifier
from app.main import app
from app.tracks import Track, TrackRepositoryUnavailable

MIGRATION_PATH = Path(__file__).parents[1] / "sql" / "001_init.sql"


@dataclass(frozen=True)
class IsolatedPostgres:
    database_url: str

    def execute(self, statement: str, parameters: tuple[object, ...] = ()) -> None:
        """Execute a setup statement using a short-lived test connection."""
        with psycopg.connect(self.database_url) as connection:
            connection.execute(statement, parameters)


@pytest.fixture(autouse=True)
def clear_dependency_overrides() -> Iterator[None]:
    """Reset FastAPI overrides and the cached auth dependency after each test."""
    yield
    app.dependency_overrides.clear()
    get_identity_verifier.cache_clear()


class StaticIdentityVerifier:
    """Return a fixed verified subject while exercising bearer dependency plumbing."""

    def __init__(self, subject: str) -> None:
        """Set the subject that every test token resolves to."""
        self._identity = VerifiedIdentity(subject=subject)

    def verify(self, token: str, /) -> VerifiedIdentity:
        """Return the configured identity for any test credential."""
        return self._identity


def _database_url_with_name(database_url: str, database_name: str) -> str:
    """Replace only the database path while preserving connection credentials."""
    parsed = urlsplit(database_url)
    return urlunsplit(parsed._replace(path=f"/{database_name}"))


@pytest.fixture
def isolated_postgres() -> Iterator[IsolatedPostgres]:
    """Create, migrate, and finally drop a unique database for one test."""
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is required for Postgres integration tests")

    test_database_name = f"audio_tracks_test_{uuid4().hex}"
    scoped_database_url = _database_url_with_name(database_url, test_database_name)
    migration = MIGRATION_PATH.read_text()

    try:
        with psycopg.connect(database_url, autocommit=True) as connection:
            connection.execute(f'CREATE DATABASE "{test_database_name}"')
    except psycopg.Error as error:
        pytest.fail(
            "TEST_DATABASE_URL must allow creation of a temporary test database: "
            f"{error.__class__.__name__}"
        )

    try:
        with psycopg.connect(scoped_database_url) as connection:
            connection.execute(migration)
        yield IsolatedPostgres(scoped_database_url)
    finally:
        with psycopg.connect(database_url, autocommit=True) as connection:
            connection.execute(f'DROP DATABASE IF EXISTS "{test_database_name}" WITH (FORCE)')


def insert_track(
    postgres: IsolatedPostgres,
    *,
    track_id: str,
    owner_id: str,
    title: str,
    duration_seconds: float,
    created_at: str,
) -> None:
    """Seed one metadata row using the migration connection, not the read-only role."""
    postgres.execute(
        """
        INSERT INTO private.tracks (id, owner_id, title, duration_seconds, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (track_id, owner_id, title, duration_seconds, created_at),
    )


def test_migration_generates_uuid_and_utc_creation_time(
    isolated_postgres: IsolatedPostgres,
):
    """The M1 migration supplies server-side UUID and timezone-aware creation defaults."""
    with psycopg.connect(isolated_postgres.database_url) as connection:
        generated_id, created_at = connection.execute(
            """
            INSERT INTO private.tracks (owner_id, title, duration_seconds)
            VALUES (%s, %s, %s)
            RETURNING id::text, created_at
            """,
            ("owner-1", "Generated metadata", 1.25),
        ).fetchone()

    assert str(UUID(generated_id)) == generated_id
    assert created_at.tzinfo is not None


@pytest.mark.parametrize("duration_seconds", [0, -1, float("inf"), float("nan")])
def test_migration_rejects_non_positive_or_non_finite_duration(
    isolated_postgres: IsolatedPostgres,
    duration_seconds: float,
):
    """The metadata constraint rejects invalid durations before they reach the reader."""
    with (
        psycopg.connect(isolated_postgres.database_url) as connection,
        pytest.raises(psycopg.errors.CheckViolation),
    ):
        connection.execute(
            """
            INSERT INTO private.tracks (owner_id, title, duration_seconds)
            VALUES (%s, %s, %s)
            """,
            ("owner-1", "Invalid duration", duration_seconds),
        )


def test_backend_role_is_read_only(isolated_postgres: IsolatedPostgres):
    """The role used by API reads cannot insert metadata."""
    with (
        psycopg.connect(isolated_postgres.database_url) as connection,
        pytest.raises(psycopg.errors.InsufficientPrivilege),
    ):
        connection.execute("SET LOCAL ROLE audio_backend")
        connection.execute(
            """
            INSERT INTO private.tracks (owner_id, title, duration_seconds)
            VALUES (%s, %s, %s)
            """,
            ("owner-1", "Forbidden write", 1),
        )


def test_empty_owner_library_returns_no_tracks(isolated_postgres: IsolatedPostgres):
    """A valid owner with no rows receives an empty repository result."""
    repository = PostgresTrackRepository(isolated_postgres.database_url)

    assert repository.list_tracks("owner-with-no-tracks") == []


def test_tracks_persist_across_repository_instances_and_are_owner_scoped(
    isolated_postgres: IsolatedPostgres,
):
    """Rows survive repository recreation and remain isolated by owner ID."""
    owner_track_id = "00000000-0000-0000-0000-000000000101"
    other_track_id = "00000000-0000-0000-0000-000000000201"
    insert_track(
        isolated_postgres,
        track_id=owner_track_id,
        owner_id="owner-1",
        title="Owner recording",
        duration_seconds=12.5,
        created_at="2026-09-11T08:00:00+00:00",
    )
    insert_track(
        isolated_postgres,
        track_id=other_track_id,
        owner_id="owner-2",
        title="Private recording",
        duration_seconds=37.25,
        created_at="2026-09-11T09:00:00+00:00",
    )

    first_repository = PostgresTrackRepository(isolated_postgres.database_url)
    second_repository = PostgresTrackRepository(isolated_postgres.database_url)

    first_owner_tracks = first_repository.list_tracks("owner-1")
    assert first_owner_tracks == [
        Track(
            id=owner_track_id,
            owner_id="owner-1",
            title="Owner recording",
            duration_seconds=12.5,
            created_at=datetime(2026, 9, 11, 8, tzinfo=UTC),
        )
    ]
    assert second_repository.list_tracks("owner-1") == first_owner_tracks
    assert second_repository.list_tracks("owner-2") == [
        Track(
            id=other_track_id,
            owner_id="owner-2",
            title="Private recording",
            duration_seconds=37.25,
            created_at=datetime(2026, 9, 11, 9, tzinfo=UTC),
        )
    ]


def test_lists_newest_first_with_id_as_tie_breaker(
    isolated_postgres: IsolatedPostgres,
):
    """The SQL ordering matches the roadmap's newest-first tie-break contract."""
    oldest_id = "00000000-0000-0000-0000-000000000001"
    lower_tie_id = "00000000-0000-0000-0000-000000000002"
    higher_tie_id = "00000000-0000-0000-0000-000000000003"
    insert_track(
        isolated_postgres,
        track_id=higher_tie_id,
        owner_id="owner-1",
        title="Higher ID",
        duration_seconds=3,
        created_at="2026-09-11T09:00:00+00:00",
    )
    insert_track(
        isolated_postgres,
        track_id=oldest_id,
        owner_id="owner-1",
        title="Oldest",
        duration_seconds=1,
        created_at="2026-09-11T08:00:00+00:00",
    )
    insert_track(
        isolated_postgres,
        track_id=lower_tie_id,
        owner_id="owner-1",
        title="Lower ID",
        duration_seconds=2,
        created_at="2026-09-11T09:00:00+00:00",
    )

    tracks = PostgresTrackRepository(isolated_postgres.database_url).list_tracks("owner-1")

    assert [track.id for track in tracks] == [higher_tie_id, lower_tie_id, oldest_id]


def test_database_query_failure_is_reported_as_repository_unavailable(
    isolated_postgres: IsolatedPostgres,
):
    """A missing table is translated to the route's dependency-failure exception."""
    repository = PostgresTrackRepository(isolated_postgres.database_url)
    isolated_postgres.execute("DROP TABLE private.tracks")

    with pytest.raises(TrackRepositoryUnavailable):
        repository.list_tracks("owner-1")


def test_tracks_endpoint_reads_the_verified_owners_persistent_library(
    isolated_postgres: IsolatedPostgres,
    monkeypatch: pytest.MonkeyPatch,
):
    """FastAPI combines bearer identity, Postgres rows, response mapping, and restart persistence."""
    insert_track(
        isolated_postgres,
        track_id="00000000-0000-0000-0000-000000000101",
        owner_id="owner-1",
        title="Visible recording",
        duration_seconds=12.5,
        created_at="2026-09-11T08:00:00+00:00",
    )
    insert_track(
        isolated_postgres,
        track_id="00000000-0000-0000-0000-000000000201",
        owner_id="owner-2",
        title="Other owner's recording",
        duration_seconds=30,
        created_at="2026-09-11T09:00:00+00:00",
    )
    monkeypatch.setenv("DATABASE_URL", isolated_postgres.database_url)
    app.dependency_overrides[get_identity_verifier] = lambda: StaticIdentityVerifier("owner-1")

    with TestClient(app) as first_client:
        first_response = first_client.get(
            "/tracks", headers={"Authorization": "Bearer valid-token"}
        )
    with TestClient(app) as restarted_client:
        restarted_response = restarted_client.get(
            "/tracks", headers={"Authorization": "Bearer valid-token"}
        )

    expected = [
        {
            "id": "00000000-0000-0000-0000-000000000101",
            "title": "Visible recording",
            "duration_seconds": 12.5,
        }
    ]
    assert first_response.status_code == 200
    assert first_response.json() == expected
    assert restarted_response.status_code == 200
    assert restarted_response.json() == expected


def test_tracks_endpoint_maps_a_database_failure_to_service_unavailable(
    isolated_postgres: IsolatedPostgres,
    monkeypatch: pytest.MonkeyPatch,
):
    """A real SQL failure becomes the documented HTTP 503 response."""
    isolated_postgres.execute("DROP TABLE private.tracks")
    monkeypatch.setenv("DATABASE_URL", isolated_postgres.database_url)
    app.dependency_overrides[get_identity_verifier] = lambda: StaticIdentityVerifier("owner-1")

    with TestClient(app) as client:
        response = client.get("/tracks", headers={"Authorization": "Bearer valid-token"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Track library unavailable"}
