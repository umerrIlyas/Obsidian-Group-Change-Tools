"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from changetools.config import Settings, get_settings


@pytest.fixture
def settings_factory(monkeypatch: pytest.MonkeyPatch) -> Iterator[type]:
    """Build a Settings instance with overrides, isolated per test.

    Usage:
        def test_x(settings_factory):
            settings = settings_factory(llm_provider="openai", openai_api_key="sk-...")
    """

    def _build(**overrides: object) -> Settings:
        for key, value in overrides.items():
            monkeypatch.setenv(key.upper(), str(value))
        get_settings.cache_clear()
        return get_settings()

    yield _build
    get_settings.cache_clear()
