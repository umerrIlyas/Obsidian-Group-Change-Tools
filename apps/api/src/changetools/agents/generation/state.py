"""Shared state for the brief-generation graph.

Plain dataclass-style models so each node accepts/returns ``dict`` patches
that LangGraph can merge. Keeping the state model dumb (no behaviour) keeps
node functions easy to test in isolation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

from changetools.domain.brand import BrandProfile
from changetools.domain.brief import BriefContent
from changetools.domain.chunk import RetrievalHit
from changetools.domain.document import Document
from changetools.domain.project import Project

SectionName = Literal[
    "executive_summary",
    "themes",
    "risks",
    "stakeholders",
    "kpis",
    "recommendations",
]

SECTION_NAMES: tuple[SectionName, ...] = (
    "executive_summary",
    "themes",
    "risks",
    "stakeholders",
    "kpis",
    "recommendations",
)

ProgressKind = Literal[
    "start",
    "context_loaded",
    "evidence_retrieved",
    "section_drafted",
    "validation_failed",
    "validated",
    "citations_scored",
    "conflicts_detected",
    "persisted",
    "error",
    "done",
]


@dataclass(slots=True)
class ProgressEvent:
    """Streamed to the SSE client between nodes."""

    kind: ProgressKind
    message: str
    detail: dict[str, Any] | None = None


class GenerationState(BaseModel):
    """LangGraph state for the generation pipeline."""

    # --- inputs ---
    project_id: uuid.UUID
    brief_id: uuid.UUID

    # --- loaded by load_context ---
    project: Project | None = None
    brand: BrandProfile | None = None
    documents: list[Document] = Field(default_factory=list)

    # --- per-section evidence ---
    evidence: dict[str, list[RetrievalHit]] = Field(default_factory=dict)

    # --- LLM draft outputs (raw dicts), keyed by section ---
    drafts: dict[str, Any] = Field(default_factory=dict)

    # --- validation control ---
    validation_errors: dict[str, str] = Field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 2

    # --- final assembled brief content ---
    content: BriefContent | None = None

    # --- meta / metrics ---
    model_name: str | None = None
    provider: str | None = None
    metrics: dict[str, float | int | str] = Field(default_factory=dict)

    # --- terminal error ---
    error: str | None = None
