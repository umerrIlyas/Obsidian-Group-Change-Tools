"""Object storage abstraction.

Local file storage is the default for dev (no Cloudflare account needed).
``S3Storage`` (compatible with R2) is used in production via env config.
"""

from changetools.infrastructure.storage.base import StorageProvider, StoredObject
from changetools.infrastructure.storage.factory import build_storage_provider

__all__ = ["StorageProvider", "StoredObject", "build_storage_provider"]
