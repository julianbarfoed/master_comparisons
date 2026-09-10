import pytest

from app.storage import InMemoryObjectStorage, ObjectNotFoundError, StoredObject


def test_storage_round_trip_preserves_content_and_media_type():
    storage = InMemoryObjectStorage()

    storage.put("audio/example.mp3", b"audio bytes", content_type="audio/mpeg")

    assert storage.get("audio/example.mp3") == StoredObject(
        content=b"audio bytes", content_type="audio/mpeg"
    )


def test_storage_replaces_an_existing_object():
    storage = InMemoryObjectStorage()
    storage.put("audio/example.mp3", b"old")

    storage.put("audio/example.mp3", b"new")

    assert storage.get("audio/example.mp3") == StoredObject(content=b"new")


def test_storage_get_reports_a_missing_object():
    storage = InMemoryObjectStorage()

    with pytest.raises(ObjectNotFoundError, match="missing.mp3"):
        storage.get("audio/missing.mp3")


def test_storage_delete_is_idempotent():
    storage = InMemoryObjectStorage()
    storage.put("audio/example.mp3", b"audio bytes")

    storage.delete("audio/example.mp3")
    storage.delete("audio/example.mp3")

    with pytest.raises(ObjectNotFoundError):
        storage.get("audio/example.mp3")
