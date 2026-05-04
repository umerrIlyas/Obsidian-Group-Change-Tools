"""Chunk — a retrievable unit of text plus its embedding."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChunkRef(BaseModel):
    """Lightweight reference to a chunk used in citations."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_filename: str | None = None
    snippet: str | None = None


class Chunk(BaseModel):
    """A retrievable text span produced by the ingestion pipeline."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    ordinal: int
    text: str
    meta: dict[str, Any] = Field(default_factory=dict)
    embedding: list[float] | None = None
    score: float | None = None  # populated by retrieval
    created_at: datetime


class RetrievalHit(BaseModel):
    """A single retrieval result — a chunk plus its document context and score."""

    chunk: Chunk
    document_filename: str
    document_kind: str
    score: float
