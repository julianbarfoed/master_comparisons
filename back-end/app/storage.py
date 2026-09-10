"""Object-storage boundary.

The HTTP layer can depend on :class:`ObjectStorage` without knowing which object
store supplies the bytes.  A Cloudflare R2 adapter can implement this contract in
a later change.
"""

from dataclasses import dataclass
from typing import Protocol


class ObjectNotFoundError(LookupError):
    """Raised when an object cannot be read from storage."""


@dataclass(frozen=True)
class StoredObject:
    """The bytes and optional media type returned by object storage."""

    content: bytes
    content_type: str | None = None


class ObjectStorage(Protocol):
    """Minimal operations required to persist opaque audio objects."""

    def put(self, key: str, content: bytes, *, content_type: str | None = None) -> None:
        """Store ``content`` under an opaque ``key``, replacing any existing object."""

    def get(self, key: str) -> StoredObject:
        """Return an object or raise :class:`ObjectNotFoundError` when it is absent."""

    def delete(self, key: str) -> None:
        """Delete an object; deleting an absent key is a no-op."""


class InMemoryObjectStorage:
    """Small storage implementation for tests and local component wiring."""

    def __init__(self) -> None:
        self._objects: dict[str, StoredObject] = {}

    def put(self, key: str, content: bytes, *, content_type: str | None = None) -> None:
        self._objects[key] = StoredObject(content=content, content_type=content_type)

    def get(self, key: str) -> StoredObject:
        try:
            return self._objects[key]
        except KeyError as error:
            raise ObjectNotFoundError(key) from error

    def delete(self, key: str) -> None:
        self._objects.pop(key, None)
