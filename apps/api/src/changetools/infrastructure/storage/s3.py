"""S3-compatible storage — used for Cloudflare R2 / AWS S3 in production."""

from __future__ import annotations

import asyncio
import io
from typing import BinaryIO

import boto3
from botocore.client import Config

from changetools.core.errors import ConfigurationError, NotFoundError, ProviderError
from changetools.infrastructure.storage.base import StoredObject


class S3Storage:
    name = "s3"

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None = None,
        access_key_id: str,
        secret_access_key: str,
        region: str = "auto",
    ) -> None:
        if not bucket:
            raise ConfigurationError("S3 bucket name is required")
        self._bucket = bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    async def put(
        self,
        *,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> StoredObject:
        kwargs: dict[str, object] = {"Bucket": self._bucket, "Key": key, "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        await asyncio.to_thread(self._client.put_object, **kwargs)
        return StoredObject(key=key, size_bytes=len(data), content_type=content_type)

    async def get(self, key: str) -> bytes:
        try:
            response = await asyncio.to_thread(
                self._client.get_object, Bucket=self._bucket, Key=key
            )
        except self._client.exceptions.NoSuchKey as exc:
            raise NotFoundError(f"Storage object not found: {key}") from exc
        except Exception as exc:  # pragma: no cover - depends on remote
            raise ProviderError(f"S3 get failed: {exc}") from exc
        return await asyncio.to_thread(response["Body"].read)

    async def open(self, key: str) -> BinaryIO:
        data = await self.get(key)
        return io.BytesIO(data)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._client.delete_object, Bucket=self._bucket, Key=key)

    async def signed_url(self, key: str, *, expires_in: int = 3600) -> str:
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
