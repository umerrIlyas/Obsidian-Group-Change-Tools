"""Document + processing-job repositories."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.document import (
    Document,
    DocumentKind,
    DocumentStatus,
    ProcessingJob,
    ProcessingJobKind,
    ProcessingStatus,
)
from changetools.repositories.models.document import DocumentORM, ProcessingJobORM


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        project_id: uuid.UUID,
        kind: DocumentKind,
        filename: str,
        content_type: str | None,
        size_bytes: int,
        storage_key: str,
        meta: dict[str, Any] | None = None,
    ) -> Document:
        row = DocumentORM(
            project_id=project_id,
            kind=kind,
            filename=filename,
            content_type=content_type,
            size_bytes=size_bytes,
            storage_key=storage_key,
            status="uploaded",
            meta=meta or {},
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return Document.model_validate(row)

    async def get(self, document_id: uuid.UUID) -> Document | None:
        row = await self._session.get(DocumentORM, document_id)
        return Document.model_validate(row) if row else None

    async def list_by_project(self, project_id: uuid.UUID) -> list[Document]:
        result = await self._session.execute(
            select(DocumentORM)
            .where(DocumentORM.project_id == project_id)
            .order_by(DocumentORM.created_at.desc())
        )
        return [Document.model_validate(r) for r in result.scalars().all()]

    async def update_status(
        self,
        document_id: uuid.UUID,
        *,
        status: DocumentStatus,
        error: str | None = None,
        raw_text: str | None = None,
        meta_patch: dict[str, Any] | None = None,
        ingested: bool = False,
    ) -> None:
        values: dict[str, Any] = {"status": status, "error": error}
        if raw_text is not None:
            values["raw_text"] = raw_text
        if ingested:
            values["ingested_at"] = datetime.now(UTC)
        if meta_patch:
            row = await self._session.get(DocumentORM, document_id)
            if row is None:
                return
            new_meta = {**(row.meta or {}), **meta_patch}
            values["meta"] = new_meta
        await self._session.execute(
            update(DocumentORM).where(DocumentORM.id == document_id).values(**values)
        )


class ProcessingJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        kind: ProcessingJobKind,
        project_id: uuid.UUID | None = None,
        document_id: uuid.UUID | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ProcessingJob:
        row = ProcessingJobORM(
            kind=kind,
            status="pending",
            project_id=project_id,
            document_id=document_id,
            meta=meta or {},
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return ProcessingJob.model_validate(row)

    async def update_status(
        self,
        job_id: uuid.UUID,
        *,
        status: ProcessingStatus,
        error: str | None = None,
        meta_patch: dict[str, Any] | None = None,
    ) -> None:
        values: dict[str, Any] = {"status": status, "error": error}
        if status == "running":
            values["started_at"] = datetime.now(UTC)
        if status in {"completed", "failed"}:
            values["finished_at"] = datetime.now(UTC)
        if meta_patch:
            row = await self._session.get(ProcessingJobORM, job_id)
            if row is None:
                return
            values["meta"] = {**(row.meta or {}), **meta_patch}
        await self._session.execute(
            update(ProcessingJobORM).where(ProcessingJobORM.id == job_id).values(**values)
        )
