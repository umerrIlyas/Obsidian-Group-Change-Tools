"""Deck — a rendered .pptx (and optional .pdf) for a Brief."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DeckStatus = Literal["rendering", "ready", "failed"]


class Deck(BaseModel):
    """A rendered deck artefact."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brief_id: uuid.UUID
    project_id: uuid.UUID
    status: DeckStatus
    pptx_storage_key: str | None = None
    pdf_storage_key: str | None = None
    slide_count: int = 0
    theme_snapshot: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
