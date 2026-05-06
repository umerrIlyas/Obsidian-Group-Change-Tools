"""Deck DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from changetools.domain.deck import DeckStatus


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_id: uuid.UUID
    project_id: uuid.UUID
    status: DeckStatus
    slide_count: int
    has_pdf: bool
    pptx_url: str | None = None
    pdf_url: str | None = None
    theme_snapshot: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
