"""Settings + config validation."""

from __future__ import annotations

import pytest

from changetools.config import Settings, get_settings


@pytest.fixture(autouse=True)
def _reset_cache() -> None:
    get_settings.cache_clear()


def test_defaults_load_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    # Clear all relevant env vars so we hit the documented defaults.
    for var in [
        "LLM_PROVIDER",
        "GROQ_API_KEY",
        "EMBEDDING_PROVIDER",
        "EMBEDDING_DIM",
        "APP_ENV",
    ]:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr("changetools.config.ENV_FILES", ())
    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    assert settings.llm_provider == "groq"
    assert settings.embedding_provider == "local"
    assert settings.embedding_dim == 384
    assert settings.app_env == "development"


def test_cors_origins_split() -> None:
    settings = Settings(
        cors_allowed_origins="http://localhost:3000, https://example.com",
        _env_file=None,  # type: ignore[call-arg]
    )
    assert settings.cors_origins == [
        "http://localhost:3000",
        "https://example.com",
    ]


def test_llm_credentials_present_per_provider() -> None:
    no_key = Settings(llm_provider="groq", _env_file=None)  # type: ignore[call-arg]
    assert no_key.llm_credentials_present() is False

    with_key = Settings(
        llm_provider="groq",
        groq_api_key="gsk_test",  # type: ignore[arg-type]
        _env_file=None,  # type: ignore[call-arg]
    )
    assert with_key.llm_credentials_present() is True

    ollama = Settings(llm_provider="ollama", _env_file=None)  # type: ignore[call-arg]
    assert ollama.llm_credentials_present() is True
