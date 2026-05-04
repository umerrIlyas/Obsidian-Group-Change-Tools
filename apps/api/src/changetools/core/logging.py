"""Structured JSON logging via structlog. Initialised once on app startup."""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import Processor

from changetools.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure stdlib logging + structlog. Idempotent."""
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    is_dev = settings.app_env == "development"
    renderer: Processor = (
        structlog.dev.ConsoleRenderer(colors=True)
        if is_dev
        else structlog.processors.JSONRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logs through structlog so uvicorn/sqlalchemy logs are formatted too.
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_StructlogStdlibFormatter(renderer))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(settings.log_level)


class _StructlogStdlibFormatter(logging.Formatter):
    """Minimal stdlib ↔ structlog bridge so uvicorn logs look the same."""

    def __init__(self, renderer: Processor) -> None:
        super().__init__()
        self._renderer = renderer

    def format(self, record: logging.LogRecord) -> str:
        event_dict: dict[str, Any] = {
            "event": record.getMessage(),
            "level": record.levelname.lower(),
            "logger": record.name,
        }
        if record.exc_info:
            event_dict["exc_info"] = record.exc_info
        rendered = self._renderer(None, record.levelname.lower(), event_dict)
        return rendered if isinstance(rendered, str) else str(rendered)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
