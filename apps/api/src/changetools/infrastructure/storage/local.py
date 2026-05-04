"""Local file-system storage — used for dev and tests."""

from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import BinaryIO

from changetools.core.errors import NotFoundError
from changetools.infrastructure.storage.base import StoredObject


class LocalFileStorage:
    name = "local"

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        # Defend against absolute keys / path traversal — keys are app-controlled, but
        # the cost of being defensive is one resolve() call.
        candidate = (self._root / key).resolve()
        if not str(candidate).startswith(str(self._root)):
            raise ValueError(f"Storage key escapes root: {key}")
        return candidate

    async def put(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return StoredObject(key=key, size_bytes=len(data), content_type=content_type)

    async def get(self, key: str) -> bytes:
        path = self._path(key)
        if not path.exists():
            raise NotFoundError(f"Storage object not found: {key}")
        return await asyncio.to_thread(path.read_bytes)

    async def open(self, key: str) -> BinaryIO:
        data = await self.get(key)
        return io.BytesIO(data)

    async def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            await asyncio.to_thread(path.unlink)

    async def signed_url(self, key: str, *, expires_in: int = 3600) -> str:
        # Dev only — points at the file on disk.
        return self._path(key).as_uri()
