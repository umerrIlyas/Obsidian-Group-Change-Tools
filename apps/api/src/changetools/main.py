"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from changetools import __version__
from changetools.api import exception_handlers
from changetools.api.routers import health
from changetools.config import Settings, get_settings
from changetools.core.logging import configure_logging, get_logger
from changetools.core.middleware import RequestContextMiddleware
from changetools.infrastructure.tracing import configure_tracing


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = get_settings()
    configure_logging(settings)
    configure_tracing(settings)
    log = get_logger("app")
    log.info(
        "app.startup",
        version=__version__,
        env=settings.app_env,
        llm_provider=settings.llm_provider,
        embedding_provider=settings.embedding_provider,
    )
    yield
    log.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ChangeTools API",
        version=__version__,
        lifespan=_lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id"],
    )
    app.add_middleware(RequestContextMiddleware)

    exception_handlers.install(app)

    app.include_router(health.router)

    return app


app = create_app()
