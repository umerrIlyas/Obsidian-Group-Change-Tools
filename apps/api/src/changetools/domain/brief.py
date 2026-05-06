"""Brief — the structured Change Strategy output.

Two layers of types live here:

* Plain content models (ExecutiveSummary, Theme, Risk, Stakeholder, KPI,
  Recommendation, Conflict) — used both by the LLM (as the structured-output
  target) and by API responses.
* Brief — the persisted aggregate that wraps content + provenance metadata.

Each evidence-bearing item carries:

  * ``evidence: list[ChunkRef]`` — pointers to chunks that ground the claim
  * ``confidence: Confidence`` — the LLM-as-judge's grounding rating

Citations are intentionally on every leaf item (not just at the brief level)
so the BriefViewer can render per-claim chips.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from changetools.domain.chunk import ChunkRef

Confidence = Literal["high", "medium", "low"]
RiskSeverity = Literal["low", "medium", "high", "critical"]
Priority = Literal["P0", "P1", "P2", "P3"]
BriefStatus = Literal["generating", "ready", "failed"]


# ---------------------------------------------------------------------------
# Section content
# ---------------------------------------------------------------------------


class ExecutiveSummary(BaseModel):
    """A few-sentence narrative for the top of the brief."""

    headline: str = Field(min_length=1, max_length=300)
    body: str = Field(min_length=1, max_length=2000)
    evidence: list[ChunkRef] = Field(default_factory=list)
    confidence: Confidence = "medium"


class Theme(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1500)
    evidence: list[ChunkRef] = Field(default_factory=list)
    confidence: Confidence = "medium"


class Risk(BaseModel):
    risk_id: str = Field(
        min_length=1,
        max_length=20,
        description="Stable identifier, e.g. R-01.",
    )
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1500)
    severity: RiskSeverity = "medium"
    likelihood: Confidence = "medium"
    owner: str | None = Field(default=None, max_length=200)
    mitigation: str | None = Field(default=None, max_length=1500)
    evidence: list[ChunkRef] = Field(default_factory=list)
    confidence: Confidence = "medium"


class Stakeholder(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)
    concern: str = Field(min_length=1, max_length=1500)
    sentiment: Literal["positive", "neutral", "concerned", "resistant"] = "neutral"
    evidence: list[ChunkRef] = Field(default_factory=list)
    confidence: Confidence = "medium"


class KPI(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    current_value: str = Field(min_length=1, max_length=200)
    target_value: str | None = Field(default=None, max_length=200)
    gap: str | None = Field(default=None, max_length=500)
    trend: str | None = Field(default=None, max_length=200)
    evidence: list[ChunkRef] = Field(default_factory=list)
    confidence: Confidence = "medium"


class Recommendation(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=1500)
    priority: Priority = "P2"
    addresses_risks: list[str] = Field(
        default_factory=list,
        description="risk_id references, e.g. ['R-01', 'R-03']",
    )
    evidence: list[ChunkRef] = Field(default_factory=list)
    confidence: Confidence = "medium"


class Conflict(BaseModel):
    """An emitted disagreement between two source chunks.

    Picked over silently choosing one side: stakeholders should see the conflict
    explicitly so they can resolve it.
    """

    topic: str = Field(min_length=1, max_length=300)
    position_a: str = Field(min_length=1, max_length=1000)
    position_b: str = Field(min_length=1, max_length=1000)
    sources_a: list[ChunkRef] = Field(default_factory=list)
    sources_b: list[ChunkRef] = Field(default_factory=list)
    suggested_resolution: str | None = Field(default=None, max_length=1500)


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------


class BriefContent(BaseModel):
    """The structured strategy brief body."""

    executive_summary: ExecutiveSummary
    themes: list[Theme] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    kpis: list[KPI] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    conflicts: list[Conflict] = Field(default_factory=list)


class Brief(BaseModel):
    """Persisted brief — content plus provenance metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    status: BriefStatus
    model_name: str | None = None
    provider: str | None = None
    content: BriefContent
    metrics: dict[str, float | int | str] = Field(default_factory=dict)
    error: str | None = None
    created_at: datetime
    updated_at: datetime
