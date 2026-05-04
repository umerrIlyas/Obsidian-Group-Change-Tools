"""Project CRUD use-cases."""

from __future__ import annotations

import uuid

from changetools.core.errors import NotFoundError
from changetools.domain.project import Project
from changetools.repositories.projects import ProjectRepository


class ProjectsService:
    def __init__(self, *, projects: ProjectRepository) -> None:
        self._projects = projects

    async def create(self, *, name: str, description: str | None = None) -> Project:
        return await self._projects.create(name=name, description=description)

    async def get(self, project_id: uuid.UUID) -> Project:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError(f"Project not found: {project_id}")
        return project

    async def list(self, *, limit: int = 100) -> list[Project]:
        return await self._projects.list(limit=limit)
