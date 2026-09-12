"""Unit coverage for the in-memory owner-scoped track reader."""

from datetime import UTC, datetime, timedelta

from app.tracks import InMemoryTrackReader, Track


def track(track_id: str, owner_id: str, *, created_at: datetime) -> Track:
    """Build a deterministic track fixture with the supplied owner and timestamp."""
    return Track(
        id=track_id,
        owner_id=owner_id,
        title=f"Track {track_id}",
        duration_seconds=12.5,
        created_at=created_at,
    )


def test_in_memory_reader_lists_only_the_owners_tracks_newest_first():
    """The in-memory adapter filters owners before applying newest-first ordering."""
    now = datetime.now(UTC)
    reader = InMemoryTrackReader(
        [
            track("00000000-0000-0000-0000-000000000001", "owner-1", created_at=now),
            track(
                "00000000-0000-0000-0000-000000000003",
                "owner-2",
                created_at=now + timedelta(seconds=1),
            ),
            track(
                "00000000-0000-0000-0000-000000000002",
                "owner-1",
                created_at=now + timedelta(seconds=1),
            ),
        ]
    )

    tracks = reader.list_tracks("owner-1")

    assert [item.id for item in tracks] == [
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000001",
    ]


def test_in_memory_reader_uses_descending_id_as_the_ordering_tiebreaker():
    """Tracks sharing a timestamp are ordered by descending UUID text."""
    created_at = datetime.now(UTC)
    reader = InMemoryTrackReader(
        [
            track("00000000-0000-0000-0000-000000000001", "owner-1", created_at=created_at),
            track("00000000-0000-0000-0000-000000000002", "owner-1", created_at=created_at),
        ]
    )

    tracks = reader.list_tracks("owner-1")

    assert [item.id for item in tracks] == [
        "00000000-0000-0000-0000-000000000002",
        "00000000-0000-0000-0000-000000000001",
    ]


def test_in_memory_reader_returns_an_empty_library_for_an_unknown_owner():
    """An owner with no rows receives the same empty result as Postgres."""
    reader = InMemoryTrackReader()

    assert reader.list_tracks("owner-without-tracks") == []
