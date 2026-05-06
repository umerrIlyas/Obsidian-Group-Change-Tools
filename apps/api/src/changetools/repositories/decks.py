"""Deck repository."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.deck import Deck, DeckStatus
from changetools.repositories.models.deck import DeckORM


class DeckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        brief_id: uuid.UUID,
        project_id: uuid.UUID,
        theme_snapshot: dict[str, Any],
    ) -> Deck:
        row = DeckORM(
            brief_id=brief_id,
            project_id=project_id,
            status="rendering",
            theme_snapshot=theme_snapshot,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return Deck.model_validate(row)

    async def update(
        self,
        deck_id: uuid.UUID,
        *,
        status: DeckStatus,
        pptx_storage_key: str | None = None,
        pdf_storage_key: str | None = None,
        slide_count: int | None = None,
        error: str | None = None,
    ) -> Deck:
        row = await self._session.get(DeckORM, deck_id)
        if row is None:
            raise LookupError(f"Deck {deck_id} not found")
        row.status = status
        if pptx_storage_key is not None:
            row.pptx_storage_key = pptx_storage_key
        if pdf_storage_key is not None:
            row.pdf_storage_key = pdf_storage_key
        if slide_count is not None:
            row.slide_count = slide_count
        row.error = error
        await self._session.flush()
        await self._session.refresh(row)
        return Deck.model_validate(row)

    async def get(self, deck_id: uuid.UUID) -> Deck | None:
        row = await self._session.get(DeckORM, deck_id)
        return Deck.model_validate(row) if row else None

    async def latest_for_brief(self, brief_id: uuid.UUID) -> Deck | None:
        result = await self._session.execute(
            select(DeckORM)
            .where(DeckORM.brief_id == brief_id)
            .order_by(desc(DeckORM.created_at))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return Deck.model_validate(row) if row else None

    async def list_by_project(self, project_id: uuid.UUID) -> list[Deck]:
        result = await self._session.execute(
            select(DeckORM)
            .where(DeckORM.project_id == project_id)
            .order_by(desc(DeckORM.created_at))
        )
        return [Deck.model_validate(r) for r in result.scalars().all()]
