"""Local sentence-transformers provider — used for free dev embeddings."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from changetools.core.logging import get_logger

if TYPE_CHECKING:  # pragma: no cover - import only for typing
    from sentence_transformers import SentenceTransformer


_log = get_logger(__name__)


class LocalSentenceTransformerEmbeddings:
    name = "local"

    def __init__(self, *, model: str, dim: int) -> None:
        self.model = model
        self.dim = dim
        self._encoder: SentenceTransformer | None = None
        self._lock = asyncio.Lock()

    async def _ensure_loaded(self) -> SentenceTransformer:
        if self._encoder is not None:
            return self._encoder
        async with self._lock:
            if self._encoder is not None:
                return self._encoder
            # Heavy import — defer to first use so app boot stays fast.
            from sentence_transformers import SentenceTransformer

            _log.info("embeddings.local.loading", model=self.model)
            encoder = await asyncio.to_thread(SentenceTransformer, self.model)
            actual_dim = encoder.get_sentence_embedding_dimension()
            if actual_dim != self.dim:
                raise ValueError(
                    f"Embedding dim mismatch: model {self.model} returns {actual_dim}, "
                    f"settings.embedding_dim is {self.dim}. Update EMBEDDING_DIM."
                )
            self._encoder = encoder
            _log.info("embeddings.local.loaded", model=self.model, dim=actual_dim)
            return encoder

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        encoder = await self._ensure_loaded()
        vectors = await asyncio.to_thread(
            encoder.encode,
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return [v.tolist() for v in vectors]

    async def embed_query(self, text: str) -> list[float]:
        result = await self.embed_documents([text])
        return result[0]
