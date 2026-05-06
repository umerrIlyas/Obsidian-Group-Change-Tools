"""Brief DTOs.

The output models mirror the persisted ``Brief`` and ``BriefContent`` shapes
verbatim — there's no projection happening between domain and API for now.
Defining them here keeps OpenAPI schema generation independent of the
internal models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from changetools.domain.brief import BriefContent, BriefStatus


class BriefSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    status: BriefStatus
    model_name: str | None
    provider: str | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class BriefOut(BriefSummaryOut):
    content: BriefContent
    metrics: dict[str, Any] = Field(default_factory=dict)
