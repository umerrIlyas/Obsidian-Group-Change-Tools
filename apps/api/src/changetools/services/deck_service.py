"""DeckService — render a Brief to .pptx (and .pdf if LibreOffice available)."""

from __future__ import annotations

import asyncio
import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.core.errors import NotFoundError
from changetools.core.logging import get_logger
from changetools.domain.brand import BrandProfile
from changetools.domain.deck import Deck
from changetools.infrastructure.rendering import (
    BrandedDeckRenderer,
    LibreOfficeMissingError,
    pptx_to_pdf,
)
from changetools.infrastructure.storage.base import StorageProvider
from changetools.repositories.brand import BrandRepository
from changetools.repositories.briefs import BriefRepository
from changetools.repositories.decks import DeckRepository
from changetools.repositories.projects import ProjectRepository

log = get_logger("deck_service")


PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


class DeckService:
    def __init__(
        self,
        *,
        sessionmaker: async_sessionmaker,  # type: ignore[type-arg]
        storage: StorageProvider,
    ) -> None:
        self._sm = sessionmaker
        self._storage = storage

    async def render_for_brief(self, brief_id: uuid.UUID) -> Deck:
        """Generate a deck for ``brief_id``. Returns the persisted Deck row.

        Always produces .pptx. PDF generation is best-effort: when LibreOffice
        isn't installed we still mark the deck ready and skip the .pdf.
        """
        # 1. Load brief, project, brand, logo.
        async with self._sm() as session:
            brief = await BriefRepository(session).get(brief_id)
            if brief is None:
                raise NotFoundError(f"Brief not found: {brief_id}")
            if brief.status != "ready":
                raise NotFoundError(
                    f"Brief is not ready (status={brief.status}); generate it first.",
                    code="brief_not_ready",
                )
            project = await ProjectRepository(session).get(brief.project_id)
            brand = await BrandRepository(session).get_for_project(brief.project_id)

        if project is None:
            raise NotFoundError(f"Project not found: {brief.project_id}")

        logo_bytes = await self._fetch_logo(brand)

        # 2. Insert placeholder deck row so the UI can poll progress.
        async with self._sm() as session:
            deck = await DeckRepository(session).create(
                brief_id=brief_id,
                project_id=brief.project_id,
                theme_snapshot=_theme_snapshot(brand),
            )
            await session.commit()

        # 3. Render pptx (CPU-bound — push to a worker thread).
        try:
            renderer = BrandedDeckRenderer(
                brand=brand,
                project_name=project.name,
                logo_bytes=logo_bytes,
            )
            pptx_bytes, slide_count = await asyncio.to_thread(renderer.render, brief)
            pptx_key = self._key(brief.project_id, deck.id, "pptx")
            await self._storage.put(key=pptx_key, data=pptx_bytes, content_type=PPTX_MIME)

            # 4. Optional PDF preview.
            pdf_key: str | None = None
            try:
                pdf_bytes = await pptx_to_pdf(pptx_bytes)
                pdf_key = self._key(brief.project_id, deck.id, "pdf")
                await self._storage.put(key=pdf_key, data=pdf_bytes, content_type="application/pdf")
            except LibreOfficeMissingError:
                log.warning(
                    "deck.pdf_skipped",
                    deck_id=str(deck.id),
                    reason="libreoffice_missing",
                )

            async with self._sm() as session:
                deck = await DeckRepository(session).update(
                    deck.id,
                    status="ready",
                    pptx_storage_key=pptx_key,
                    pdf_storage_key=pdf_key,
                    slide_count=slide_count,
                )
                await session.commit()
            return deck

        except Exception as exc:
            log.exception("deck.render_failed", deck_id=str(deck.id))
            async with self._sm() as session:
                await DeckRepository(session).update(
                    deck.id, status="failed", error=str(exc)[:2000]
                )
                await session.commit()
            raise

    async def get(self, deck_id: uuid.UUID) -> Deck:
        async with self._sm() as session:
            deck = await DeckRepository(session).get(deck_id)
        if deck is None:
            raise NotFoundError(f"Deck not found: {deck_id}")
        return deck

    async def latest_for_brief(self, brief_id: uuid.UUID) -> Deck | None:
        async with self._sm() as session:
            return await DeckRepository(session).latest_for_brief(brief_id)

    async def fetch_pptx(self, deck_id: uuid.UUID) -> tuple[bytes, str]:
        deck = await self.get(deck_id)
        if not deck.pptx_storage_key:
            raise NotFoundError("Deck has no .pptx artefact")
        data = await self._storage.get(deck.pptx_storage_key)
        return data, PPTX_MIME

    async def fetch_pdf(self, deck_id: uuid.UUID) -> tuple[bytes, str]:
        deck = await self.get(deck_id)
        if not deck.pdf_storage_key:
            raise NotFoundError(
                "Deck has no PDF preview (LibreOffice not available)",
                code="no_pdf",
            )
        data = await self._storage.get(deck.pdf_storage_key)
        return data, "application/pdf"

    async def _fetch_logo(self, brand: BrandProfile | None) -> bytes | None:
        if brand is None or not brand.logo_storage_key:
            return None
        try:
            return await self._storage.get(brand.logo_storage_key)
        except NotFoundError:
            return None

    @staticmethod
    def _key(project_id: uuid.UUID, deck_id: uuid.UUID, ext: str) -> str:
        return f"projects/{project_id}/decks/{deck_id}.{ext}"


def _theme_snapshot(brand: BrandProfile | None) -> dict:
    """Capture the brand state used for rendering so we can audit later."""
    if brand is None:
        return {"used_default_palette": True}
    return {
        "primary_color": brand.primary_color,
        "secondary_color": brand.secondary_color,
        "accent_color": brand.accent_color,
        "neutrals": brand.neutrals.model_dump(),
        "font_heading": brand.font_heading,
        "font_body": brand.font_body,
    }
