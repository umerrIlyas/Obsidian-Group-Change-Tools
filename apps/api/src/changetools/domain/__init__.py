"""Pydantic domain models — DTOs that flow between services, the API, and the repos.

These intentionally do NOT depend on SQLAlchemy. Repository implementations
convert between these and ORM rows at the persistence boundary.
"""

from changetools.domain.brand import OBSIDIAN_PRESET, BrandProfile, HexColor, Neutrals
from changetools.domain.chunk import Chunk, ChunkRef
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
    "OBSIDIAN_PRESET",
    "BrandProfile",
    "Chunk",
    "ChunkRef",
    "Document",
    "DocumentKind",
    "DocumentStatus",
    "HexColor",
    "Neutrals",
    "ProcessingJob",
    "ProcessingJobKind",
    "ProcessingStatus",
    "Project",
]
