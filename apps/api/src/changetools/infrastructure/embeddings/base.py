"""Embedding provider Protocol."""

from __future__ import annotations

from typing import Protocol


class EmbeddingProvider(Protocol):
    """Encodes text into fixed-size vectors.

    The dimension is exposed as a property so callers can configure pgvector columns
    or fail fast when the configured dim doesn't match the persisted schema.
    """

    name: str
    model: str
    dim: int

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch of documents."""
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Encode a single retrieval query."""
        ...
