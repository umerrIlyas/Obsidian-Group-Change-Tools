"""LLM provider factory selection + missing-credential handling."""

from __future__ import annotations

import pytest

from changetools.config import Settings
from changetools.core.errors import ConfigurationError
from changetools.infrastructure.llm import build_llm_provider


def test_groq_provider_built_with_key() -> None:
    settings = Settings(
        llm_provider="groq",
        groq_api_key="gsk_test",  # type: ignore[arg-type]
        _env_file=None,  # type: ignore[call-arg]
    )
    provider = build_llm_provider(settings)
    assert provider.name == "groq"
    assert provider.model == settings.groq_model


def test_groq_provider_missing_key_raises() -> None:
    settings = Settings(llm_provider="groq", _env_file=None)  # type: ignore[call-arg]
    with pytest.raises(ConfigurationError, match="GROQ_API_KEY"):
        build_llm_provider(settings)


def test_openai_provider_built_with_key() -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key="sk-test",  # type: ignore[arg-type]
        _env_file=None,  # type: ignore[call-arg]
    )
    provider = build_llm_provider(settings)
    assert provider.name == "openai"


def test_openai_provider_missing_key_raises() -> None:
    settings = Settings(llm_provider="openai", _env_file=None)  # type: ignore[call-arg]
    with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
        build_llm_provider(settings)


def test_anthropic_provider_built_with_key() -> None:
    settings = Settings(
        llm_provider="anthropic",
        anthropic_api_key="sk-ant-test",  # type: ignore[arg-type]
        _env_file=None,  # type: ignore[call-arg]
    )
    provider = build_llm_provider(settings)
    assert provider.name == "anthropic"


def test_ollama_provider_no_key_required() -> None:
    settings = Settings(llm_provider="ollama", _env_file=None)  # type: ignore[call-arg]
    provider = build_llm_provider(settings)
    assert provider.name == "ollama"
