"""Embedding-provider abstraction.

Two concrete providers ship today: ``LocalSentenceTransformerEmbeddings``
(CPU-friendly, free, used for local dev) and ``OpenAIEmbeddings`` (used in prod).
The factory selects between them based on ``Settings.embedding_provider``.
"""

from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.infrastructure.embeddings.factory import build_embedding_provider

__all__ = ["EmbeddingProvider", "build_embedding_provider"]
