"""Persistence layer.

``models`` holds the SQLAlchemy ORM mappings. Each repository module exposes
a class that takes an ``AsyncSession`` and returns Pydantic domain models —
ORM rows never escape the repository layer.
"""

from changetools.repositories.brand import BrandRepository
from changetools.repositories.briefs import BriefRepository
from changetools.repositories.chat import ChatRepository
from changetools.repositories.chunks import ChunkRepository
from changetools.repositories.decks import DeckRepository
from changetools.repositories.documents import DocumentRepository, ProcessingJobRepository
from changetools.repositories.projects import ProjectRepository

__all__ = [
    "BrandRepository",
    "BriefRepository",
    "ChatRepository",
    "ChunkRepository",
    "DeckRepository",
    "DocumentRepository",
    "ProcessingJobRepository",
    "ProjectRepository",
]
