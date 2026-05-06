"""Persist the final BriefContent + metrics back to the briefs row."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.agents.generation.state import GenerationState
from changetools.repositories.briefs import BriefRepository


def make_persist_node(sm: async_sessionmaker):  # type: ignore[type-arg]
    async def persist_node(state: GenerationState) -> dict:
        if state.content is None:
            raise RuntimeError("persist_node called with no content")
        async with sm() as session:
            await BriefRepository(session).update_content(
                state.brief_id,
                status="ready",
                content=state.content,
                metrics=state.metrics,
                error=None,
            )
            await session.commit()
        return {}

    return persist_node


persist_node = make_persist_node
