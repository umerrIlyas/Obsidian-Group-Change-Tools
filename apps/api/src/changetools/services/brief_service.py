"""BriefService — orchestrates the generation graph.

The service is responsible for:

* creating the placeholder ``briefs`` row (status = generating)
* invoking the compiled LangGraph and yielding progress events
* mapping graph errors back to a failed brief row

The router consumes ``stream()`` to fan progress out via SSE; tests can
consume the same generator synchronously.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.agents.generation import build_generation_graph
from changetools.agents.generation.state import GenerationState, ProgressEvent
from changetools.core.errors import NotFoundError
from changetools.core.logging import get_logger
from changetools.domain.brief import Brief
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.infrastructure.llm.base import LLMProvider
from changetools.repositories.briefs import BriefRepository
from changetools.repositories.documents import DocumentRepository
from changetools.repositories.projects import ProjectRepository

log = get_logger("brief_service")


class BriefService:
    def __init__(
        self,
        *,
        sessionmaker: async_sessionmaker,  # type: ignore[type-arg]
        llm: LLMProvider,
        embeddings: EmbeddingProvider,
    ) -> None:
        self._sm = sessionmaker
        self._llm = llm
        self._embeddings = embeddings

    async def list_for_project(self, project_id: uuid.UUID) -> list[Brief]:
        async with self._sm() as session:
            return await BriefRepository(session).list_by_project(project_id)

    async def get(self, brief_id: uuid.UUID) -> Brief:
        async with self._sm() as session:
            brief = await BriefRepository(session).get(brief_id)
        if brief is None:
            raise NotFoundError(f"Brief not found: {brief_id}")
        return brief

    async def create_placeholder(self, project_id: uuid.UUID) -> Brief:
        async with self._sm() as session:
            project = await ProjectRepository(session).get(project_id)
            if project is None:
                raise NotFoundError(f"Project not found: {project_id}")
            ready_docs = [
                d
                for d in await DocumentRepository(session).list_by_project(project_id)
                if d.status == "ready"
            ]
            if not ready_docs:
                raise NotFoundError(
                    "No ingested documents for this project — upload + wait for ready first",
                    code="no_ready_documents",
                )
            brief = await BriefRepository(session).create(
                project_id=project_id,
                status="generating",
                model_name=self._llm.model,
                provider=self._llm.name,
            )
            await session.commit()
        return brief

    async def stream(
        self, *, project_id: uuid.UUID, brief_id: uuid.UUID
    ) -> AsyncIterator[ProgressEvent]:
        """Run the graph and yield progress events as nodes complete.

        Final event is either ``done`` (with brief_id) or ``error``.
        """
        graph = build_generation_graph(
            sessionmaker=self._sm, llm=self._llm, embeddings=self._embeddings
        )
        initial = GenerationState(project_id=project_id, brief_id=brief_id)
        started = time.perf_counter()

        yield ProgressEvent("start", "Loading project context…")

        try:
            # ``astream`` with stream_mode="updates" gives us {node_name: state_patch}
            # after each node finishes — perfect for progress events.
            async for update in graph.astream(initial, stream_mode="updates"):
                for node_name, _patch in update.items():
                    yield _event_for_node(node_name)
        except Exception as exc:
            log.exception("brief.generation_failed", brief_id=str(brief_id))
            await self._mark_failed(brief_id, repr(exc))
            yield ProgressEvent("error", f"Generation failed: {exc}")
            return

        elapsed = round(time.perf_counter() - started, 1)
        yield ProgressEvent(
            "done",
            f"Brief ready ({elapsed}s)",
            detail={"brief_id": str(brief_id), "elapsed_seconds": elapsed},
        )

    async def _mark_failed(self, brief_id: uuid.UUID, error: str) -> None:
        async with self._sm() as session:
            await BriefRepository(session).mark_failed(brief_id, error[:2000])
            await session.commit()


# Map a node name to a user-facing progress message.
_NODE_MESSAGES: dict[str, tuple[str, str]] = {
    "load_context": ("context_loaded", "Loaded project, brand, and documents"),
    "retrieve_evidence": ("evidence_retrieved", "Retrieved evidence from RAG index"),
    "draft_sections": ("section_drafted", "Drafted brief sections"),
    "validate": ("validated", "Validated section schemas"),
    "cite_evidence": ("citations_scored", "Resolved citations and confidence"),
    "detect_conflicts": ("conflicts_detected", "Scanned for source conflicts"),
    "assemble": ("validated", "Assembled brief"),
    "persist": ("persisted", "Saved brief"),
}


def _event_for_node(node_name: str) -> ProgressEvent:
    kind, message = _NODE_MESSAGES.get(node_name, ("section_drafted", f"Step: {node_name}"))
    return ProgressEvent(kind, message, detail={"node": node_name})  # type: ignore[arg-type]
