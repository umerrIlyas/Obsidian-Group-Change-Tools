"""Document + retrieval DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DocumentSummaryOut(BaseModel):
    """Lightweight projection used in lists — omits raw_text + meta."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    kind: str
    filename: str
    content_type: str | None
    size_bytes: int
    status: str
    error: str | None
    ingested_at: datetime | None
    created_at: datetime


class DocumentOut(DocumentSummaryOut):
    """Detail projection — includes meta + raw text excerpt."""

    raw_text_excerpt: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class RetrieveIn(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(8, ge=1, le=50)


class RetrievedHit(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str
    document_kind: str
    score: float
    text: str
    meta: dict[str, Any] = Field(default_factory=dict)


class RetrieveOut(BaseModel):
    query: str
    hits: list[RetrievedHit]
