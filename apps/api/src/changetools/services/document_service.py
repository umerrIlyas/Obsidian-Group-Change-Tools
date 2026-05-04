"""DocumentService — file uploads, listing, and triggering ingestion."""

from __future__ import annotations

import uuid

from changetools.core.errors import NotFoundError, ValidationError
from changetools.domain.document import Document, DocumentKind
from changetools.infrastructure.storage.base import StorageProvider
from changetools.repositories.documents import DocumentRepository
from changetools.repositories.projects import ProjectRepository

# Map common content types / extensions to our DocumentKind enum.
_KIND_BY_EXTENSION: dict[str, DocumentKind] = {
    ".docx": "docx",
    ".xlsx": "xlsx",
    ".pdf": "pdf",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".webp": "image",
    ".svg": "image",
}


def infer_document_kind(filename: str) -> DocumentKind:
    lower = filename.lower()
    for ext, kind in _KIND_BY_EXTENSION.items():
        if lower.endswith(ext):
            return kind
    return "other"


class DocumentService:
    def __init__(
        self,
        *,
        documents: DocumentRepository,
        projects: ProjectRepository,
        storage: StorageProvider,
    ) -> None:
        self._documents = documents
        self._projects = projects
        self._storage = storage

    async def upload(
        self,
        *,
        project_id: uuid.UUID,
        filename: str,
        content_type: str | None,
        data: bytes,
    ) -> Document:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError(f"Project not found: {project_id}")

        if not data:
            raise ValidationError("Uploaded file is empty.")

        kind = infer_document_kind(filename)
        document_id = uuid.uuid4()
        storage_key = f"projects/{project_id}/documents/{document_id}/{filename}"
        await self._storage.put(key=storage_key, data=data, content_type=content_type)

        return await self._documents.create(
            project_id=project_id,
            kind=kind,
            filename=filename,
            content_type=content_type,
            size_bytes=len(data),
            storage_key=storage_key,
        )

    async def get(self, document_id: uuid.UUID) -> Document:
        doc = await self._documents.get(document_id)
        if doc is None:
            raise NotFoundError(f"Document not found: {document_id}")
        return doc

    async def list_by_project(self, project_id: uuid.UUID) -> list[Document]:
        return await self._documents.list_by_project(project_id)
