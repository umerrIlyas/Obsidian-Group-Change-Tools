"""Anthropic adapter — used in production when ``LLM_PROVIDER=anthropic``."""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from changetools.core.errors import ConfigurationError


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, *, api_key: str, model: str) -> None:
        if not api_key:
            raise ConfigurationError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic",
                code="missing_anthropic_key",
            )
        self._api_key = api_key
        self.model = model

    def chat_model(
        self,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> BaseChatModel:
        return ChatAnthropic(
            api_key=self._api_key,
            model_name=self.model,
            temperature=temperature,
            max_tokens=max_tokens or 4096,
        )
