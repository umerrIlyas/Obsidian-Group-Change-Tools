"""LLM-facing draft schemas.

These mirror the persisted ``BriefContent`` shapes, but evidence is captured
as bare ``cited_chunk_ids: list[str]`` rather than ``ChunkRef`` objects.
The graph maps these strings back to typed ``ChunkRef`` instances after
the LLM call returns.

Why two layers? Letting the LLM emit fully-typed ChunkRef objects (with
document_id, snippet, etc.) wastes tokens and invites hallucination. Asking
for a UUID list is cheap and easy to validate.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from changetools.domain.brief import Confidence, Priority, RiskSeverity


class DraftExecutiveSummary(BaseModel):
    headline: str
    body: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class DraftTheme(BaseModel):
    title: str
    description: str
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class DraftThemes(BaseModel):
    items: list[DraftTheme]


class DraftRisk(BaseModel):
    risk_id: str
    title: str
    description: str
    severity: RiskSeverity = "medium"
    likelihood: Confidence = "medium"
    owner: str | None = None
    mitigation: str | None = None
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class DraftRisks(BaseModel):
    items: list[DraftRisk]


class DraftStakeholder(BaseModel):
    name: str
    role: str
    concern: str
    sentiment: Literal["positive", "neutral", "concerned", "resistant"] = "neutral"
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class DraftStakeholders(BaseModel):
    items: list[DraftStakeholder]


class DraftKPI(BaseModel):
    name: str
    current_value: str
    target_value: str | None = None
    gap: str | None = None
    trend: str | None = None
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class DraftKPIs(BaseModel):
    items: list[DraftKPI]


class DraftRecommendation(BaseModel):
    title: str
    description: str
    priority: Priority = "P2"
    addresses_risks: list[str] = Field(default_factory=list)
    cited_chunk_ids: list[str] = Field(default_factory=list)
    confidence: Confidence = "medium"


class DraftRecommendations(BaseModel):
    items: list[DraftRecommendation]


class DraftConflict(BaseModel):
    topic: str
    position_a: str
    position_b: str
    sources_a_chunk_ids: list[str] = Field(default_factory=list)
    sources_b_chunk_ids: list[str] = Field(default_factory=list)
    suggested_resolution: str | None = None


class DraftConflicts(BaseModel):
    items: list[DraftConflict]


# Section name → its draft schema
SECTION_SCHEMAS: dict[str, type[BaseModel]] = {
    "executive_summary": DraftExecutiveSummary,
    "themes": DraftThemes,
    "risks": DraftRisks,
    "stakeholders": DraftStakeholders,
    "kpis": DraftKPIs,
    "recommendations": DraftRecommendations,
}
