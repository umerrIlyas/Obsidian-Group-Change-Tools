"""Chunk repository — bulk insert + vector similarity retrieval."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.chunk import Chunk, RetrievalHit
from changetools.repositories.models.chunk import ChunkORM
from changetools.repositories.models.document import DocumentORM


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def bulk_insert(
        self,
        *,
        document_id: uuid.UUID,
        chunks: list[tuple[str, dict[str, Any], list[float] | None]],
        starting_ordinal: int = 0,
    ) -> int:
        """Insert ``chunks`` for a document. Returns count inserted.

        Each tuple is ``(text, meta, embedding)``. ``embedding`` may be ``None`` for a
        first pass that defers vectorisation to a later stage.
        """
        if not chunks:
            return 0
        rows = [
            ChunkORM(
                document_id=document_id,
                ordinal=starting_ordinal + i,
                text=text,
                meta=meta,
                embedding=embedding,
            )
            for i, (text, meta, embedding) in enumerate(chunks)
        ]
        self._session.add_all(rows)
        await self._session.flush()
        return len(rows)

    async def list_by_document(self, document_id: uuid.UUID) -> list[Chunk]:
        result = await self._session.execute(
            select(ChunkORM).where(ChunkORM.document_id == document_id).order_by(ChunkORM.ordinal)
        )
        return [Chunk.model_validate(r) for r in result.scalars().all()]

    async def search(
        self,
        *,
        project_id: uuid.UUID,
        embedding: list[float],
        top_k: int = 8,
    ) -> list[RetrievalHit]:
        """Cosine-similarity search across all ready documents in a project.

        Returns the top-K most similar chunks, each with parent-document context
        and a similarity score (1.0 == identical, 0.0 == orthogonal).
        """
        distance = ChunkORM.embedding.cosine_distance(embedding)
        stmt = (
            select(
                ChunkORM,
                DocumentORM.filename,
                DocumentORM.kind,
                distance.label("distance"),
            )
            .join(DocumentORM, DocumentORM.id == ChunkORM.document_id)
            .where(
                DocumentORM.project_id == project_id,
                DocumentORM.status == "ready",
                ChunkORM.embedding.is_not(None),
            )
            .order_by(distance.asc())
            .limit(top_k)
        )
        result = await self._session.execute(stmt)
        hits: list[RetrievalHit] = []
        for chunk_row, filename, kind, dist in result.all():
            chunk = Chunk.model_validate(chunk_row)
            score = 1.0 - float(dist)
            chunk.score = score
            hits.append(
                RetrievalHit(
                    chunk=chunk,
                    document_filename=filename,
                    document_kind=kind,
                    score=score,
                )
            )
        return hits
