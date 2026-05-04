"""OpenAI embeddings — production embedding provider."""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings as LCOpenAIEmbeddings

from changetools.core.errors import ConfigurationError


class OpenAIEmbeddingsProvider:
    name = "openai"

    def __init__(
        self, *, api_key: str, model: str = "text-embedding-3-small", dim: int = 1536
    ) -> None:
        if not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai",
                code="missing_openai_key",
            )
        self.model = model
        self.dim = dim
        self._client = LCOpenAIEmbeddings(api_key=api_key, model=model, dimensions=dim)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return await self._client.aembed_documents(texts)

    async def embed_query(self, text: str) -> list[float]:
        return await self._client.aembed_query(text)
