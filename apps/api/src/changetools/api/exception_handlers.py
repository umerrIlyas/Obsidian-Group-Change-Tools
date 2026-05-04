"""Translate domain exceptions to JSON error responses."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from changetools.core.errors import ChangeToolsError
from changetools.core.logging import get_logger

_log = get_logger("api.errors")


def install(app: FastAPI) -> None:
    @app.exception_handler(ChangeToolsError)
    async def _handle_domain(_: Request, exc: ChangeToolsError) -> JSONResponse:
        _log.warning("domain.error", code=exc.code, message=str(exc))
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )
