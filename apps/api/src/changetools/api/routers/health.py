"""Liveness + readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from changetools import __version__
from changetools.config import Settings, get_settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    app_env: str
    llm_provider: str
    llm_credentials: bool
    embedding_provider: str
    embedding_dim: int
    tracing_enabled: bool


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Cheap, dependency-free liveness probe.

    Returns the configured providers so a smoke-test can confirm the env is wired
    correctly without exposing secrets.
    """
    settings: Settings = get_settings()
    return HealthResponse(
        status="ok",
        version=__version__,
        app_env=settings.app_env,
        llm_provider=settings.llm_provider,
        llm_credentials=settings.llm_credentials_present(),
        embedding_provider=settings.embedding_provider,
        embedding_dim=settings.embedding_dim,
        tracing_enabled=settings.langchain_tracing_v2,
    )
