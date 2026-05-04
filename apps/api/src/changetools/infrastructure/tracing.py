"""LangSmith tracing setup.

LangChain reads tracing config from a handful of LANGCHAIN_* env vars on import.
We mirror them from our typed Settings object on app startup so a single .env
file remains the source of truth.
"""

from __future__ import annotations

import os

from changetools.config import Settings
from changetools.core.logging import get_logger

_log = get_logger(__name__)


def configure_tracing(settings: Settings) -> None:
    """Populate LangChain's expected env vars. No-op when tracing is disabled."""
    if not settings.langchain_tracing_v2:
        _log.info("tracing.disabled")
        return

    if settings.langchain_api_key is None:
        _log.warning("tracing.misconfigured", reason="LANGCHAIN_API_KEY missing")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key.get_secret_value()
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    _log.info("tracing.enabled", project=settings.langchain_project)
