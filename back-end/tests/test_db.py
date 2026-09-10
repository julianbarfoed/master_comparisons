import pytest

from app.db import AudioRecord, DuplicateAudioRecordError, InMemoryAudioRepository


def audio_record() -> AudioRecord:
    return AudioRecord(
        id="audio-1",
        owner_id="owner-1",
        object_key="uploads/audio-1.wav",
        title="First recording",
    )


def test_create_and_get_audio_record():
    repository = InMemoryAudioRepository()
    record = audio_record()

    repository.create(record)

    assert repository.get_by_id(record.id) == record


def test_get_missing_audio_record_returns_none():
    repository = InMemoryAudioRepository()

    assert repository.get_by_id("missing") is None


def test_create_rejects_duplicate_id_without_replacing_record():
    repository = InMemoryAudioRepository()
    original = audio_record()
    duplicate = AudioRecord(
        id=original.id,
        owner_id="owner-2",
        object_key="uploads/replacement.wav",
        title="Replacement",
    )
    repository.create(original)

    with pytest.raises(DuplicateAudioRecordError) as error:
        repository.create(duplicate)

    assert error.value.record_id == original.id
    assert repository.get_by_id(original.id) == original
