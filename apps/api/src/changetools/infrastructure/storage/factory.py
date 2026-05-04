"""Storage provider selection.

Production sets ``R2_*`` env vars and gets ``S3Storage``. Dev falls back to
``LocalFileStorage`` rooted at ``./storage/`` next to the repo.
"""

from __future__ import annotations

from pathlib import Path

from changetools.config import Settings
from changetools.core.logging import get_logger
from changetools.infrastructure.storage.base import StorageProvider
from changetools.infrastructure.storage.local import LocalFileStorage
from changetools.infrastructure.storage.s3 import S3Storage

_log = get_logger(__name__)


def build_storage_provider(settings: Settings) -> StorageProvider:
    if settings.r2_access_key_id and settings.r2_secret_access_key and settings.r2_endpoint:
        _log.info("storage.s3.configured", bucket=settings.r2_bucket)
        return S3Storage(
            bucket=settings.r2_bucket,
            endpoint_url=settings.r2_endpoint,
            access_key_id=settings.r2_access_key_id.get_secret_value(),
            secret_access_key=settings.r2_secret_access_key.get_secret_value(),
        )
    root = Path("storage").resolve()
    _log.info("storage.local.configured", root=str(root))
    return LocalFileStorage(root)
