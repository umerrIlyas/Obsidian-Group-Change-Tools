"""Project repository — CRUD against the ``projects`` table."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.project import Project
from changetools.repositories.models.project import ProjectORM


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, name: str, description: str | None = None) -> Project:
        row = ProjectORM(name=name, description=description)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return Project.model_validate(row)

    async def get(self, project_id: uuid.UUID) -> Project | None:
        row = await self._session.get(ProjectORM, project_id)
        return Project.model_validate(row) if row else None

    async def list(self, *, limit: int = 100) -> list[Project]:
        result = await self._session.execute(
            select(ProjectORM).order_by(ProjectORM.created_at.desc()).limit(limit)
        )
        return [Project.model_validate(r) for r in result.scalars().all()]
