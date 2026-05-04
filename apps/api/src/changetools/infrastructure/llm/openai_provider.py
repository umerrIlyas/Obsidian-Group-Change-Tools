"""OpenAI adapter — used in production when ``LLM_PROVIDER=openai``."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from changetools.core.errors import ConfigurationError


class OpenAIProvider:
    name = "openai"

    def __init__(self, *, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai",
                code="missing_openai_key",
            )
        self._api_key = api_key
        self.model = model

    def chat_model(
        self,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> BaseChatModel:
        return ChatOpenAI(
            api_key=self._api_key,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
