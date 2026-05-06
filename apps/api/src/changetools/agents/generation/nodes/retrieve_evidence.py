"""Run per-section retrieval queries against pgvector in parallel."""

from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.agents.generation.evidence import SECTION_QUERIES
from changetools.agents.generation.state import GenerationState
from changetools.domain.chunk import RetrievalHit
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.services.retrieval_service import RetrievalService

PER_QUERY_K = 8


def make_retrieve_evidence_node(
    sm: async_sessionmaker,  # type: ignore[type-arg]
    embeddings: EmbeddingProvider,
):
    async def retrieve_evidence_node(state: GenerationState) -> dict:
        # Each parallel task gets its own session — async sessions are not
        # safe for concurrent ops, so we can't share one across asyncio.gather.
        async def query(section: str, q: str) -> tuple[str, list[RetrievalHit]]:
            async with sm() as session:
                service = RetrievalService(session=session, embeddings=embeddings)
                hits = await service.retrieve(
                    project_id=state.project_id, query=q, top_k=PER_QUERY_K
                )
            return section, hits

        tasks: list[asyncio.Task] = []  # type: ignore[type-arg]
        for section, queries in SECTION_QUERIES.items():
            for q in queries:
                tasks.append(asyncio.create_task(query(section, q)))
        results = await asyncio.gather(*tasks)

        # Merge per-section hits, deduping by chunk_id, keeping highest score.
        evidence: dict[str, dict] = {sec: {} for sec in SECTION_QUERIES}
        for section, hits in results:
            bucket = evidence[section]
            for hit in hits:
                existing = bucket.get(hit.chunk.id)
                if existing is None or hit.score > existing.score:
                    bucket[hit.chunk.id] = hit

        merged = {section: list(b.values()) for section, b in evidence.items()}
        # Trim to top 12 per section by score.
        for section, hits_list in merged.items():
            hits_list.sort(key=lambda h: h.score, reverse=True)
            merged[section] = hits_list[:12]

        total_unique = len({h.chunk.id for hits_list in merged.values() for h in hits_list})

        return {
            "evidence": merged,
            "metrics": {**state.metrics, "evidence_chunks": total_unique},
        }

    return retrieve_evidence_node


retrieve_evidence_node = make_retrieve_evidence_node
