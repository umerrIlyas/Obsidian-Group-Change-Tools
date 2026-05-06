"""Chat session + message repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.chat import ChatMessage, ChatRole, ChatSession, ToolCall
from changetools.repositories.models.chat import ChatMessageORM, ChatSessionORM


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # --- sessions ---

    async def create_session(
        self, *, project_id: uuid.UUID, title: str | None = None
    ) -> ChatSession:
        row = ChatSessionORM(project_id=project_id, title=title)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return ChatSession.model_validate(row)

    async def get_session(self, session_id: uuid.UUID) -> ChatSession | None:
        row = await self._session.get(ChatSessionORM, session_id)
        return ChatSession.model_validate(row) if row else None

    async def list_sessions_by_project(self, project_id: uuid.UUID) -> list[ChatSession]:
        result = await self._session.execute(
            select(ChatSessionORM)
            .where(ChatSessionORM.project_id == project_id)
            .order_by(desc(ChatSessionORM.updated_at))
        )
        return [ChatSession.model_validate(r) for r in result.scalars().all()]

    async def latest_session_for_project(self, project_id: uuid.UUID) -> ChatSession | None:
        result = await self._session.execute(
            select(ChatSessionORM)
            .where(ChatSessionORM.project_id == project_id)
            .order_by(desc(ChatSessionORM.updated_at))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return ChatSession.model_validate(row) if row else None

    async def touch_session(self, session_id: uuid.UUID) -> None:
        from sqlalchemy import func

        await self._session.execute(
            update(ChatSessionORM)
            .where(ChatSessionORM.id == session_id)
            .values(updated_at=func.now())
        )

    # --- messages ---

    async def add_message(
        self,
        *,
        session_id: uuid.UUID,
        role: ChatRole,
        content: str = "",
        tool_calls: list[ToolCall] | None = None,
        tool_call_id: str | None = None,
        tool_name: str | None = None,
        meta: dict[str, Any] | None = None,
    ) -> ChatMessage:
        row = ChatMessageORM(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=[tc.model_dump() for tc in (tool_calls or [])],
            tool_call_id=tool_call_id,
            tool_name=tool_name,
            meta=meta or {},
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return self._message_to_domain(row)

    async def list_messages(self, session_id: uuid.UUID) -> list[ChatMessage]:
        result = await self._session.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at)
        )
        return [self._message_to_domain(r) for r in result.scalars().all()]

    @staticmethod
    def _message_to_domain(row: ChatMessageORM) -> ChatMessage:
        return ChatMessage(
            id=row.id,
            session_id=row.session_id,
            role=row.role,  # type: ignore[arg-type]
            content=row.content,
            tool_calls=[ToolCall.model_validate(tc) for tc in (row.tool_calls or [])],
            tool_call_id=row.tool_call_id,
            tool_name=row.tool_name,
            meta=row.meta or {},
            created_at=row.created_at,
        )
