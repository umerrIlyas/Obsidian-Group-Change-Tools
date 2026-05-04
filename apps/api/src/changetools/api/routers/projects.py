"""Project CRUD endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status

from changetools.api.deps import get_projects_service
from changetools.api.schemas import CreateProjectIn, ProjectOut
from changetools.services.projects_service import ProjectsService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectOut)
async def create_project(
    body: CreateProjectIn,
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectOut:
    project = await service.create(name=body.name, description=body.description)
    return ProjectOut.model_validate(project)


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    service: ProjectsService = Depends(get_projects_service),
) -> list[ProjectOut]:
    projects = await service.list()
    return [ProjectOut.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: uuid.UUID,
    service: ProjectsService = Depends(get_projects_service),
) -> ProjectOut:
    project = await service.get(project_id)
    return ProjectOut.model_validate(project)
