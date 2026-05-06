"""Brief generation + retrieval endpoints.

POST creates a placeholder row and streams progress over SSE while the graph
runs. GET endpoints return the persisted state.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict, is_dataclass
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from changetools.api.deps import get_brief_service
from changetools.api.schemas import BriefOut, BriefSummaryOut
from changetools.services.brief_service import BriefService

router = APIRouter(tags=["briefs"])


@router.post(
    "/projects/{project_id}/brief",
    status_code=status.HTTP_200_OK,
)
async def generate_brief(
    project_id: uuid.UUID,
    service: BriefService = Depends(get_brief_service),
) -> StreamingResponse:
    """Generate a brief and stream progress as SSE.

    The first event is the placeholder ``brief_id`` so the client can
    navigate to the brief page even before generation finishes.
    """
    brief = await service.create_placeholder(project_id)

    async def event_stream() -> AsyncIterator[bytes]:
        # Send the brief_id as the first event so the client can stash it
        # and start polling/loading the eventual brief.
        head = {"kind": "started", "brief_id": str(brief.id), "version": brief.version}
        yield _sse(head)

        async for ev in service.stream(project_id=project_id, brief_id=brief.id):
            payload = {
                "kind": ev.kind,
                "message": ev.message,
                "brief_id": str(brief.id),
                "detail": ev.detail or {},
            }
            yield _sse(payload)
            # let the OS flush — uvicorn writes the chunk on yield boundary
        # Stream end — empty event so the EventSource closes cleanly.
        yield b"event: end\ndata: {}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx, Render)
        },
    )


@router.get(
    "/projects/{project_id}/briefs",
    response_model=list[BriefSummaryOut],
)
async def list_briefs(
    project_id: uuid.UUID,
    service: BriefService = Depends(get_brief_service),
) -> list[BriefSummaryOut]:
    items = await service.list_for_project(project_id)
    return [BriefSummaryOut.model_validate(b) for b in items]


@router.get(
    "/briefs/{brief_id}",
    response_model=BriefOut,
)
async def get_brief(
    brief_id: uuid.UUID,
    service: BriefService = Depends(get_brief_service),
) -> BriefOut:
    brief = await service.get(brief_id)
    return BriefOut.model_validate(brief)


def _sse(payload: dict[str, Any] | object) -> bytes:
    """Serialize a payload as a single SSE ``data:`` event."""
    if isinstance(payload, dict):
        body = payload
    elif is_dataclass(payload) and not isinstance(payload, type):
        body = asdict(payload)
    else:
        body = {"data": str(payload)}
    return f"data: {json.dumps(body, default=str)}\n\n".encode()
