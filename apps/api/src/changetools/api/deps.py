"""FastAPI dependency injection.

Process-wide singletons are cached with ``lru_cache``; per-request resources
(DB session, services that take a session) are wired via FastAPI's ``Depends``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from changetools.config import Settings, get_settings
from changetools.db import get_engine
from changetools.infrastructure.embeddings import (
    EmbeddingProvider,
    build_embedding_provider,
)
from changetools.infrastructure.llm import LLMProvider, build_llm_provider
from changetools.infrastructure.storage import StorageProvider, build_storage_provider
from changetools.repositories.brand import BrandRepository
from changetools.repositories.documents import (
    DocumentRepository,
    ProcessingJobRepository,
)
from changetools.repositories.projects import ProjectRepository
from changetools.services.brand_service import BrandService
from changetools.services.brief_service import BriefService
from changetools.services.chat_service import ChatService
from changetools.services.deck_service import DeckService
from changetools.services.document_service import DocumentService
from changetools.services.ingestion_service import IngestionService
from changetools.services.projects_service import ProjectsService
from changetools.services.retrieval_service import RetrievalService

# --- process-wide singletons ---


@lru_cache(maxsize=1)
def get_storage() -> StorageProvider:
    return build_storage_provider(get_settings())


@lru_cache(maxsize=1)
def get_embeddings() -> EmbeddingProvider:
    return build_embedding_provider(get_settings())


@lru_cache(maxsize=1)
def get_llm() -> LLMProvider:
    return build_llm_provider(get_settings())


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    return IngestionService(
        sessionmaker=get_sessionmaker(),
        storage=get_storage(),
        embeddings=get_embeddings(),
    )


@lru_cache(maxsize=1)
def get_brief_service() -> BriefService:
    return BriefService(
        sessionmaker=get_sessionmaker(),
        llm=get_llm(),
        embeddings=get_embeddings(),
    )


@lru_cache(maxsize=1)
def get_deck_service() -> DeckService:
    return DeckService(
        sessionmaker=get_sessionmaker(),
        storage=get_storage(),
    )


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService(
        sessionmaker=get_sessionmaker(),
        llm=get_llm(),
        embeddings=get_embeddings(),
        deck_service=get_deck_service(),
    )


# --- per-request ---


async def get_db() -> AsyncIterator[AsyncSession]:
    sm = get_sessionmaker()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_settings_dep() -> Settings:
    return get_settings()


def get_projects_service(
    session: AsyncSession = Depends(get_db),
) -> ProjectsService:
    return ProjectsService(projects=ProjectRepository(session))


def get_document_service(
    session: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage),
) -> DocumentService:
    return DocumentService(
        documents=DocumentRepository(session),
        projects=ProjectRepository(session),
        storage=storage,
    )


def get_processing_jobs(
    session: AsyncSession = Depends(get_db),
) -> ProcessingJobRepository:
    return ProcessingJobRepository(session)


def get_retrieval_service(
    session: AsyncSession = Depends(get_db),
    embeddings: EmbeddingProvider = Depends(get_embeddings),
) -> RetrievalService:
    return RetrievalService(session=session, embeddings=embeddings)


def get_brand_service(
    session: AsyncSession = Depends(get_db),
    storage: StorageProvider = Depends(get_storage),
) -> BrandService:
    return BrandService(
        brand=BrandRepository(session),
        projects=ProjectRepository(session),
        storage=storage,
    )
