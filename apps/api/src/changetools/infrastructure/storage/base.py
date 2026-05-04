"""Storage provider Protocol — file persistence + retrieval."""

from __future__ import annotations

from typing import BinaryIO, Protocol

from pydantic import BaseModel


class StoredObject(BaseModel):
    key: str
    size_bytes: int
    content_type: str | None = None


class StorageProvider(Protocol):
    """Persists and retrieves binary blobs by opaque key."""

    name: str

    async def put(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredObject: ...

    async def get(self, key: str) -> bytes: ...

    async def open(self, key: str) -> BinaryIO:
        """Return a binary file-like for streaming consumers (parsers)."""
        ...

    async def delete(self, key: str) -> None: ...

    async def signed_url(self, key: str, *, expires_in: int = 3600) -> str:
        """Return a temporary download URL. Local storage may return a file:// URL."""
        ...
