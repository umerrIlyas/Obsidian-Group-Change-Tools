"""Project — top-level container for documents, brand, briefs, decks, chats."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Project(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str = Field(..., max_length=200)
    description: str | None = None
    created_at: datetime
    updated_at: datetime
