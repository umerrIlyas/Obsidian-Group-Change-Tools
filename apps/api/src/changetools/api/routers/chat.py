"""Chat endpoints — sessions, history, SSE message streaming."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from changetools.api.deps import get_chat_service
from changetools.api.schemas import ChatMessageOut, ChatSessionOut, SendMessageIn
from changetools.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@router.get(
    "/projects/{project_id}/chat/sessions",
    response_model=list[ChatSessionOut],
)
async def list_sessions(
    project_id: uuid.UUID,
    service: ChatService = Depends(get_chat_service),
) -> list[ChatSessionOut]:
    sessions = await service.list_sessions(project_id)
    return [ChatSessionOut.model_validate(s) for s in sessions]


@router.post(
    "/projects/{project_id}/chat/sessions",
    response_model=ChatSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    project_id: uuid.UUID,
    service: ChatService = Depends(get_chat_service),
) -> ChatSessionOut:
    s = await service.get_or_create_session(project_id, session_id=None)
    return ChatSessionOut.model_validate(s)


@router.get(
    "/projects/{project_id}/chat/sessions/{session_id}/messages",
    response_model=list[ChatMessageOut],
)
async def list_messages(
    project_id: uuid.UUID,
    session_id: uuid.UUID,
    service: ChatService = Depends(get_chat_service),
) -> list[ChatMessageOut]:
    # Verify the session belongs to the project (raises 404 otherwise).
    await service.get_or_create_session(project_id, session_id=session_id)
    messages = await service.list_messages(session_id)
    return [ChatMessageOut.model_validate(m) for m in messages]


@router.post("/projects/{project_id}/chat/messages")
async def send_message(
    project_id: uuid.UUID,
    body: SendMessageIn,
    service: ChatService = Depends(get_chat_service),
) -> StreamingResponse:
    """Send a message and stream the agent's response (tokens + tool calls) via SSE."""
    sess = await service.get_or_create_session(project_id, session_id=body.session_id)

    async def event_stream() -> AsyncIterator[bytes]:
        head = {"kind": "session", "session_id": str(sess.id)}
        yield _sse(head)

        async for ev in service.stream_response(
            project_id=project_id,
            session_id=sess.id,
            user_message=body.message,
        ):
            yield _sse({"kind": ev.kind, **ev.detail})

        yield b"event: end\ndata: {}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(payload: dict) -> bytes:
    return f"data: {json.dumps(payload, default=str)}\n\n".encode()
