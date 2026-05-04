"""Selects the configured embedding provider based on ``Settings.embedding_provider``."""

from __future__ import annotations

from changetools.config import Settings
from changetools.core.errors import ConfigurationError
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.infrastructure.embeddings.local import LocalSentenceTransformerEmbeddings
from changetools.infrastructure.embeddings.openai import OpenAIEmbeddingsProvider

# Default dim per known model — used so settings.embedding_dim acts as a sanity check.
_OPENAI_DIMS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    match settings.embedding_provider:
        case "local":
            return LocalSentenceTransformerEmbeddings(
                model=settings.embedding_model_local,
                dim=settings.embedding_dim,
            )
        case "openai":
            api_key = settings.openai_api_key
            if api_key is None:
                raise ConfigurationError(
                    "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai"
                )
            model = "text-embedding-3-small"
            dim = _OPENAI_DIMS.get(model, settings.embedding_dim)
            return OpenAIEmbeddingsProvider(
                api_key=api_key.get_secret_value(),
                model=model,
                dim=dim,
            )
    raise ConfigurationError(  # pragma: no cover
        f"Unknown EMBEDDING_PROVIDER: {settings.embedding_provider}"
    )
