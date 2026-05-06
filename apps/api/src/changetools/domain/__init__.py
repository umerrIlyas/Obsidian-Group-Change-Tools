"""Pydantic domain models — DTOs that flow between services, the API, and the repos.

These intentionally do NOT depend on SQLAlchemy. Repository implementations
convert between these and ORM rows at the persistence boundary.
"""

from changetools.domain.brand import OBSIDIAN_PRESET, BrandProfile, HexColor, Neutrals
from changetools.domain.brief import (
    KPI,
    Brief,
    BriefContent,
    BriefStatus,
    Confidence,
    Conflict,
    ExecutiveSummary,
    Priority,
    Recommendation,
    Risk,
    RiskSeverity,
    Stakeholder,
    Theme,
)
from changetools.domain.chat import ChatMessage, ChatRole, ChatSession, ToolCall
from changetools.domain.chunk import Chunk, ChunkRef
from changetools.domain.deck import Deck, DeckStatus
from changetools.domain.document import (
    Document,
    DocumentKind,
    DocumentStatus,
    ProcessingJob,
    ProcessingJobKind,
    ProcessingStatus,
)
from changetools.domain.project import Project

__all__ = [
    "KPI",
    "OBSIDIAN_PRESET",
    "BrandProfile",
    "Brief",
    "BriefContent",
    "BriefStatus",
    "ChatMessage",
    "ChatRole",
    "ChatSession",
    "Chunk",
    "ChunkRef",
    "Confidence",
    "Conflict",
    "Deck",
    "DeckStatus",
    "Document",
    "DocumentKind",
    "DocumentStatus",
    "ExecutiveSummary",
    "HexColor",
    "Neutrals",
    "Priority",
    "ProcessingJob",
    "ProcessingJobKind",
    "ProcessingStatus",
    "Project",
    "Recommendation",
    "Risk",
    "RiskSeverity",
    "Stakeholder",
    "Theme",
    "ToolCall",
]
