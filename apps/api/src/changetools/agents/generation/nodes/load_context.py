"""Load project, brand, and document summaries from the DB."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.agents.generation.state import GenerationState
from changetools.repositories.brand import BrandRepository
from changetools.repositories.documents import DocumentRepository
from changetools.repositories.projects import ProjectRepository


def make_load_context_node(sm: async_sessionmaker):  # type: ignore[type-arg]
    async def load_context_node(state: GenerationState) -> dict:
        async with sm() as session:
            project = await ProjectRepository(session).get(state.project_id)
            brand = await BrandRepository(session).get_for_project(state.project_id)
            documents = [
                d
                for d in await DocumentRepository(session).list_by_project(state.project_id)
                if d.status == "ready"
            ]
        return {
            "project": project,
            "brand": brand,
            "documents": documents,
        }

    return load_context_node


# Re-exported for symmetry with the other nodes.
load_context_node = make_load_context_node
