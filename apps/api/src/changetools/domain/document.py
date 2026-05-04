"""Document + processing-job domain models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

DocumentKind = Literal["docx", "xlsx", "pdf", "image", "other"]
DocumentStatus = Literal[
    "uploaded",
    "parsing",
    "chunking",
    "embedding",
    "ready",
    "failed",
]
ProcessingJobKind = Literal["ingest", "generate_brief", "render_deck"]
ProcessingStatus = Literal["pending", "running", "completed", "failed"]


class Document(BaseModel):
    """Source material uploaded by the user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    kind: DocumentKind
    filename: str = Field(..., max_length=500)
    content_type: str | None = None
    size_bytes: int = Field(0, ge=0)
    storage_key: str
    status: DocumentStatus
    error: str | None = None
    raw_text: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    ingested_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProcessingJob(BaseModel):
    """Tracks an async pipeline run (ingestion, generation, rendering)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: ProcessingJobKind
    status: ProcessingStatus
    project_id: uuid.UUID | None = None
    document_id: uuid.UUID | None = None
    error: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
