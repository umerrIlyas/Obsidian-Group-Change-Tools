"""Ollama adapter — placeholder for self-hosted OSS models in production.

Imports the OSS-friendly ``ChatOllama`` lazily so the dep stays optional.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel


class OllamaProvider:
    name = "ollama"

    def __init__(self, *, base_url: str, model: str) -> None:
        self._base_url = base_url
        self.model = model

    def chat_model(
        self,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> BaseChatModel:
        # Lazy import — ``langchain-community`` is heavy and Ollama is rarely active in dev.
        from langchain_community.chat_models import ChatOllama

        return ChatOllama(
            base_url=self._base_url,
            model=self.model,
            temperature=temperature,
            num_predict=max_tokens or -1,
        )
