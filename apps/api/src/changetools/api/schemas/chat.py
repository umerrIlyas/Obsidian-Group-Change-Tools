"""Chat DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from changetools.domain.chat import ChatRole, ToolCall


class ChatSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: ChatRole
    content: str
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None
    tool_name: str | None
    meta: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SendMessageIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000)
    session_id: uuid.UUID | None = None
