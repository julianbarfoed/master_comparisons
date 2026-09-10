"""Provider-neutral persistence boundary for audio metadata."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AudioRecord:
    """The minimum metadata needed to connect an owner to stored audio."""

    id: str
    owner_id: str
    object_key: str
    title: str


class DuplicateAudioRecordError(Exception):
    """Raised when a repository already contains the requested record ID."""

    def __init__(self, record_id: str) -> None:
        self.record_id = record_id
        super().__init__(f"audio record already exists: {record_id}")


class AudioRepository(Protocol):
    """Persistence operations required by the first audio metadata slice."""

    def create(self, record: AudioRecord) -> None:
        """Persist a new record or raise ``DuplicateAudioRecordError``."""
        ...

    def get_by_id(self, record_id: str) -> AudioRecord | None:
        """Return a record by ID, or ``None`` when it does not exist."""
        ...


class InMemoryAudioRepository:
    """Small dependency-free repository for tests and local composition."""

    def __init__(self) -> None:
        self._records: dict[str, AudioRecord] = {}

    def create(self, record: AudioRecord) -> None:
        if record.id in self._records:
            raise DuplicateAudioRecordError(record.id)

        self._records[record.id] = record

    def get_by_id(self, record_id: str) -> AudioRecord | None:
        return self._records.get(record_id)
