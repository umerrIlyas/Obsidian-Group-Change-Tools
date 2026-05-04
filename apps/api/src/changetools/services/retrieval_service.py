"""RetrievalService — embed a query and return top-K matching chunks."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.chunk import RetrievalHit
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.repositories.chunks import ChunkRepository


class RetrievalService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        embeddings: EmbeddingProvider,
    ) -> None:
        self._session = session
        self._embeddings = embeddings

    async def retrieve(
        self,
        *,
        project_id: uuid.UUID,
        query: str,
        top_k: int = 8,
    ) -> list[RetrievalHit]:
        if not query.strip():
            return []
        vector = await self._embeddings.embed_query(query)
        return await ChunkRepository(self._session).search(
            project_id=project_id, embedding=vector, top_k=top_k
        )
