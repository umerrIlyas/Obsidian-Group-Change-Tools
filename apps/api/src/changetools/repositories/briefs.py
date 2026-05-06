"""Brief repository — versioned writes per project."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.brief import Brief, BriefContent, BriefStatus, ExecutiveSummary
from changetools.repositories.models.brief import BriefORM


class BriefRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        project_id: uuid.UUID,
        status: BriefStatus,
        model_name: str | None = None,
        provider: str | None = None,
    ) -> Brief:
        version = await self._next_version(project_id)
        row = BriefORM(
            project_id=project_id,
            version=version,
            status=status,
            model_name=model_name,
            provider=provider,
            content={},
            metrics={},
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return self._to_domain(row)

    async def update_content(
        self,
        brief_id: uuid.UUID,
        *,
        status: BriefStatus,
        content: BriefContent,
        metrics: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> Brief:
        row = await self._session.get(BriefORM, brief_id)
        if row is None:
            raise LookupError(f"Brief {brief_id} not found")
        row.status = status
        row.content = content.model_dump(mode="json")
        if metrics is not None:
            row.metrics = metrics
        row.error = error
        await self._session.flush()
        await self._session.refresh(row)
        return self._to_domain(row)

    async def mark_failed(self, brief_id: uuid.UUID, error: str) -> None:
        row = await self._session.get(BriefORM, brief_id)
        if row is None:
            return
        row.status = "failed"
        row.error = error
        await self._session.flush()

    async def get(self, brief_id: uuid.UUID) -> Brief | None:
        row = await self._session.get(BriefORM, brief_id)
        return self._to_domain(row) if row else None

    async def list_by_project(self, project_id: uuid.UUID) -> list[Brief]:
        result = await self._session.execute(
            select(BriefORM)
            .where(BriefORM.project_id == project_id)
            .order_by(desc(BriefORM.version))
        )
        return [self._to_domain(r) for r in result.scalars().all()]

    async def latest_for_project(self, project_id: uuid.UUID) -> Brief | None:
        result = await self._session.execute(
            select(BriefORM)
            .where(BriefORM.project_id == project_id)
            .order_by(desc(BriefORM.version))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def _next_version(self, project_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.coalesce(func.max(BriefORM.version), 0)).where(
                BriefORM.project_id == project_id
            )
        )
        return int(result.scalar_one() or 0) + 1

    @staticmethod
    def _to_domain(row: BriefORM) -> Brief:
        # An in-flight brief may have empty/partial content; default to a stub
        # so consumers always see a valid `BriefContent` structure.
        content_data = row.content or {}
        if "executive_summary" not in content_data:
            content = BriefContent(
                executive_summary=ExecutiveSummary(
                    headline="(generating)",
                    body="(generating)",
                )
            )
        else:
            content = BriefContent.model_validate(content_data)
        return Brief(
            id=row.id,
            project_id=row.project_id,
            version=row.version,
            status=row.status,  # type: ignore[arg-type]
            model_name=row.model_name,
            provider=row.provider,
            content=content,
            metrics=row.metrics or {},
            error=row.error,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
