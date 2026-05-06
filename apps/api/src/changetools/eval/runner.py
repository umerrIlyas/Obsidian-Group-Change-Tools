"""Eval orchestrator.

Loads a brief from the database (latest for a project, or by explicit id),
materializes an ``EvalContext`` (the project's chunks indexed by id), runs
all cases, and writes the markdown report.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from changetools.config import Settings, get_settings
from changetools.core.errors import NotFoundError
from changetools.db import get_engine
from changetools.domain.brief import Brief
from changetools.domain.chunk import Chunk
from changetools.eval.cases import EvalContext, EvalResult, all_cases
from changetools.eval.report import render_markdown, write_report
from changetools.repositories.briefs import BriefRepository
from changetools.repositories.models import ChunkORM, DocumentORM
from changetools.repositories.projects import ProjectRepository


async def _load_chunks_for_project(
    session: AsyncSession, project_id: uuid.UUID
) -> dict[uuid.UUID, Chunk]:
    """Load every chunk in a project, keyed by chunk_id, for citation checks."""
    result = await session.execute(
        select(ChunkORM)
        .join(DocumentORM, DocumentORM.id == ChunkORM.document_id)
        .where(DocumentORM.project_id == project_id)
    )
    out: dict[uuid.UUID, Chunk] = {}
    for row in result.scalars().all():
        out[row.id] = Chunk.model_validate(row)
    return out


async def run_eval(
    *,
    project_id: uuid.UUID,
    brief_id: uuid.UUID | None = None,
    output_path: Path,
) -> tuple[bool, list[EvalResult], Brief]:
    settings: Settings = get_settings()
    sm: async_sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)

    started = time.perf_counter()

    async with sm() as session:
        project = await ProjectRepository(session).get(project_id)
        if project is None:
            raise NotFoundError(f"Project not found: {project_id}")

        if brief_id is None:
            brief = await BriefRepository(session).latest_for_project(project_id)
            if brief is None:
                raise NotFoundError(
                    "No brief exists for this project. Generate one before running eval.",
                    code="no_brief",
                )
        else:
            brief = await BriefRepository(session).get(brief_id)
            if brief is None:
                raise NotFoundError(f"Brief not found: {brief_id}")

        chunks_by_id = await _load_chunks_for_project(session, project_id)

    ctx = EvalContext(chunks_by_id=chunks_by_id, project_chunk_count=len(chunks_by_id))

    results = [case(brief, ctx) for case in all_cases()]
    elapsed = time.perf_counter() - started

    md = render_markdown(
        brief=brief,
        project_id=project_id,
        project_name=project.name,
        results=results,
        settings=settings,
        elapsed_seconds=elapsed,
    )
    write_report(output_path, md)

    overall_pass = all(r.passed for r in results)
    return overall_pass, results, brief


__all__ = ["run_eval"]
