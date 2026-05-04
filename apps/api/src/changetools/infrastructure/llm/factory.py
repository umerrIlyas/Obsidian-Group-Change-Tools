"""Selects the configured LLM provider based on ``Settings.llm_provider``."""

from __future__ import annotations

from changetools.config import Settings
from changetools.core.errors import ConfigurationError
from changetools.infrastructure.llm.anthropic_provider import AnthropicProvider
from changetools.infrastructure.llm.base import LLMProvider
from changetools.infrastructure.llm.groq_provider import GroqProvider
from changetools.infrastructure.llm.ollama_provider import OllamaProvider
from changetools.infrastructure.llm.openai_provider import OpenAIProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    """Return a configured ``LLMProvider`` for the current environment."""
    match settings.llm_provider:
        case "groq":
            return GroqProvider(
                api_key=_secret(settings.groq_api_key, "GROQ_API_KEY"),
                model=settings.groq_model,
            )
        case "openai":
            return OpenAIProvider(
                api_key=_secret(settings.openai_api_key, "OPENAI_API_KEY"),
                model=settings.openai_model,
            )
        case "anthropic":
            return AnthropicProvider(
                api_key=_secret(settings.anthropic_api_key, "ANTHROPIC_API_KEY"),
                model=settings.anthropic_model,
            )
        case "ollama":
            return OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
            )
    raise ConfigurationError(  # pragma: no cover - exhaustive match
        f"Unknown LLM_PROVIDER: {settings.llm_provider}"
    )


def _secret(value: object, env_name: str) -> str:
    """Coerce a SecretStr | None to a plain string, raising if missing."""
    if value is None:
        raise ConfigurationError(
            f"{env_name} is required for the configured LLM provider",
            code="missing_credentials",
        )
    # SecretStr exposes its value via .get_secret_value()
    return value.get_secret_value() if hasattr(value, "get_secret_value") else str(value)
