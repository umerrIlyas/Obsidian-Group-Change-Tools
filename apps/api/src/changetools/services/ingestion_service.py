"""IngestionService — orchestrates parse → chunk → embed → persist for a document.

Designed to run as a FastAPI BackgroundTask. Each call opens its own session via
the injected ``async_sessionmaker`` so it is independent of the request lifecycle.
The document's ``status`` column is the state machine consumers poll.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from changetools.core.errors import NotFoundError
from changetools.core.logging import get_logger
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.infrastructure.parsing import parse_document
from changetools.infrastructure.storage.base import StorageProvider
from changetools.repositories.chunks import ChunkRepository
from changetools.repositories.documents import DocumentRepository
from changetools.services.chunking_service import ChunkingService

_log = get_logger(__name__)


class IngestionService:
    def __init__(
        self,
        *,
        sessionmaker: async_sessionmaker[AsyncSession],
        storage: StorageProvider,
        embeddings: EmbeddingProvider,
        chunking: ChunkingService | None = None,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._storage = storage
        self._embeddings = embeddings
        self._chunking = chunking or ChunkingService()

    async def process(self, document_id: uuid.UUID) -> None:
        """Run the ingestion pipeline. Failures are recorded on the document row."""
        try:
            await self._run(document_id)
        except Exception as exc:
            _log.exception("ingestion.failed", document_id=str(document_id))
            await self._mark_failed(document_id, repr(exc))

    # --- internal ---

    async def _run(self, document_id: uuid.UUID) -> None:
        # 1. Load + transition to parsing
        async with self._sessionmaker() as session:
            doc_repo = DocumentRepository(session)
            doc = await doc_repo.get(document_id)
            if doc is None:
                raise NotFoundError(f"Document not found: {document_id}")
            await doc_repo.update_status(document_id, status="parsing")
            await session.commit()

        _log.info(
            "ingestion.started",
            document_id=str(document_id),
            filename=doc.filename,
            kind=doc.kind,
        )

        # 2. Fetch + parse (no DB session needed during parsing)
        stream = await self._storage.open(doc.storage_key)
        parsed = parse_document(stream, filename=doc.filename)

        # 3. Persist raw_text + parser meta, transition to chunking
        async with self._sessionmaker() as session:
            doc_repo = DocumentRepository(session)
            await doc_repo.update_status(
                document_id,
                status="chunking",
                raw_text=parsed.raw_text,
                meta_patch={"parser": parsed.meta},
            )
            await session.commit()

        # 4. Chunk
        seeds = self._chunking.chunk(parsed, doc.kind)
        if not seeds:
            async with self._sessionmaker() as session:
                doc_repo = DocumentRepository(session)
                await doc_repo.update_status(
                    document_id,
                    status="ready",
                    ingested=True,
                    meta_patch={"chunk_count": 0},
                )
                await session.commit()
            return

        # 5. Embed (potentially heavy — own no DB lock)
        async with self._sessionmaker() as session:
            doc_repo = DocumentRepository(session)
            await doc_repo.update_status(document_id, status="embedding")
            await session.commit()

        texts = [s.text for s in seeds]
        vectors = await self._embeddings.embed_documents(texts)

        # 6. Persist chunks + mark ready
        async with self._sessionmaker() as session:
            chunk_repo = ChunkRepository(session)
            doc_repo = DocumentRepository(session)
            payload = [(s.text, s.meta, v) for s, v in zip(seeds, vectors, strict=True)]
            inserted = await chunk_repo.bulk_insert(document_id=document_id, chunks=payload)
            await doc_repo.update_status(
                document_id,
                status="ready",
                ingested=True,
                meta_patch={"chunk_count": inserted},
            )
            await session.commit()

        _log.info(
            "ingestion.completed",
            document_id=str(document_id),
            chunk_count=inserted,
        )

    async def _mark_failed(self, document_id: uuid.UUID, error: str) -> None:
        try:
            async with self._sessionmaker() as session:
                doc_repo = DocumentRepository(session)
                await doc_repo.update_status(document_id, status="failed", error=error[:5000])
                await session.commit()
        except Exception:  # pragma: no cover - last-ditch logging
            _log.exception("ingestion.failed.recording_error", document_id=str(document_id))
