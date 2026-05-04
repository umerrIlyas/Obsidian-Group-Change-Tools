"""LocalFileStorage round-trip tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from changetools.core.errors import NotFoundError
from changetools.infrastructure.storage.local import LocalFileStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path)


async def test_put_and_get_roundtrip(storage: LocalFileStorage) -> None:
    obj = await storage.put(key="docs/sample.txt", data=b"hello world", content_type="text/plain")
    assert obj.size_bytes == 11
    assert await storage.get("docs/sample.txt") == b"hello world"


async def test_get_missing_raises(storage: LocalFileStorage) -> None:
    with pytest.raises(NotFoundError):
        await storage.get("does/not/exist.bin")


async def test_path_traversal_rejected(storage: LocalFileStorage) -> None:
    with pytest.raises(ValueError, match="escapes root"):
        await storage.put(key="../escape.txt", data=b"bad")


async def test_signed_url_returns_file_uri(storage: LocalFileStorage) -> None:
    await storage.put(key="docs/sample.txt", data=b"hi")
    url = await storage.signed_url("docs/sample.txt")
    assert url.startswith("file://")
