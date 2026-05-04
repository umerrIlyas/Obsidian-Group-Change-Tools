"""HTTP middleware — request_id propagation + access logging."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from changetools.core.logging import get_logger

REQUEST_ID_HEADER = "X-Request-Id"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request-scoped id + timing to every request, log access lines."""

    def __init__(self, app: Callable[..., Awaitable[None]]) -> None:
        super().__init__(app)
        self._log = get_logger("http.access")

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        token = structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            self._log.exception("request.failed", duration_ms=round(duration_ms, 1))
            structlog.contextvars.reset_contextvars(**token)
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        self._log.info(
            "request.completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 1),
        )
        structlog.contextvars.reset_contextvars(**token)
        return response
