"""Groq adapter — uses ``langchain-groq``."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq

from changetools.core.errors import ConfigurationError


class GroqProvider:
    name = "groq"

    def __init__(self, *, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "GROQ_API_KEY is required when LLM_PROVIDER=groq",
                code="missing_groq_key",
            )
        self._api_key = api_key
        self.model = model

    def chat_model(
        self,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> BaseChatModel:
        return ChatGroq(
            api_key=self._api_key,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
