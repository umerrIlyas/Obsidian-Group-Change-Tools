"""Deck endpoints — generate, fetch, download."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from fastapi.responses import Response

from changetools.api.deps import get_deck_service
from changetools.api.schemas import DeckOut
from changetools.domain.deck import Deck
from changetools.services.deck_service import PPTX_MIME, DeckService

router = APIRouter(tags=["decks"])


def _to_out(d: Deck) -> DeckOut:
    return DeckOut(
        id=d.id,
        brief_id=d.brief_id,
        project_id=d.project_id,
        status=d.status,
        slide_count=d.slide_count,
        has_pdf=d.pdf_storage_key is not None,
        pptx_url=f"/decks/{d.id}/pptx" if d.pptx_storage_key else None,
        pdf_url=f"/decks/{d.id}/preview.pdf" if d.pdf_storage_key else None,
        theme_snapshot=d.theme_snapshot,
        error=d.error,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


@router.post(
    "/briefs/{brief_id}/deck",
    response_model=DeckOut,
    status_code=status.HTTP_201_CREATED,
)
async def generate_deck(
    brief_id: uuid.UUID,
    service: DeckService = Depends(get_deck_service),
) -> DeckOut:
    deck = await service.render_for_brief(brief_id)
    return _to_out(deck)


@router.get("/briefs/{brief_id}/deck", response_model=DeckOut)
async def get_latest_deck(
    brief_id: uuid.UUID,
    service: DeckService = Depends(get_deck_service),
) -> DeckOut | None:
    deck = await service.latest_for_brief(brief_id)
    if deck is None:
        return None
    return _to_out(deck)


@router.get("/decks/{deck_id}", response_model=DeckOut)
async def get_deck(
    deck_id: uuid.UUID,
    service: DeckService = Depends(get_deck_service),
) -> DeckOut:
    deck = await service.get(deck_id)
    return _to_out(deck)


@router.get("/decks/{deck_id}/pptx")
async def download_pptx(
    deck_id: uuid.UUID,
    service: DeckService = Depends(get_deck_service),
) -> Response:
    data, content_type = await service.fetch_pptx(deck_id)
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="deck-{deck_id}.pptx"',
            "Cache-Control": "private, max-age=300",
        },
    )


@router.get("/decks/{deck_id}/preview.pdf")
async def download_pdf(
    deck_id: uuid.UUID,
    service: DeckService = Depends(get_deck_service),
) -> Response:
    data, content_type = await service.fetch_pdf(deck_id)
    return Response(
        content=data,
        media_type=content_type,
        headers={
            "Content-Disposition": f'inline; filename="deck-{deck_id}.pdf"',
            "Cache-Control": "private, max-age=300",
        },
    )


__all__ = ["PPTX_MIME", "router"]
