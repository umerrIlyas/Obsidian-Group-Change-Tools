"""Brand profile endpoints."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response

from changetools.api.deps import get_brand_service
from changetools.api.schemas import (
    BrandProfileOut,
    PaletteSuggestion,
    PaletteSuggestionOut,
    UpdateBrandIn,
)
from changetools.core.errors import NotFoundError
from changetools.domain.brand import Neutrals
from changetools.services.brand_service import BrandService

router = APIRouter(prefix="/projects", tags=["brand"])


def _to_out(profile, request_path_id: uuid.UUID) -> BrandProfileOut:
    return BrandProfileOut(
        id=profile.id,
        project_id=profile.project_id,
        primary_color=profile.primary_color,
        secondary_color=profile.secondary_color,
        accent_color=profile.accent_color,
        neutrals=profile.neutrals,
        font_heading=profile.font_heading,
        font_body=profile.font_body,
        logo_url=(f"/projects/{request_path_id}/brand/logo" if profile.logo_storage_key else None),
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


@router.get("/{project_id}/brand", response_model=BrandProfileOut)
async def get_brand(
    project_id: uuid.UUID,
    service: BrandService = Depends(get_brand_service),
) -> BrandProfileOut:
    profile = await service.get_for_project(project_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "not_found", "message": "No brand profile yet."}},
        )
    return _to_out(profile, project_id)


@router.put("/{project_id}/brand", response_model=BrandProfileOut)
async def update_brand(
    project_id: uuid.UUID,
    body: UpdateBrandIn,
    service: BrandService = Depends(get_brand_service),
) -> BrandProfileOut:
    profile = await service.save(
        project_id=project_id,
        primary_color=body.primary_color,
        secondary_color=body.secondary_color,
        accent_color=body.accent_color,
        neutrals=body.neutrals,
        font_heading=body.font_heading,
        font_body=body.font_body,
    )
    return _to_out(profile, project_id)


@router.post("/{project_id}/brand", response_model=BrandProfileOut)
async def update_brand_with_logo(
    project_id: uuid.UUID,
    payload: str = Form(..., description="JSON-encoded UpdateBrandIn"),
    logo: UploadFile | None = File(None),
    service: BrandService = Depends(get_brand_service),
) -> BrandProfileOut:
    """Multipart endpoint — used when uploading a logo alongside palette/font."""
    body = UpdateBrandIn.model_validate(json.loads(payload))
    logo_bytes: bytes | None = None
    logo_filename: str | None = None
    logo_content_type: str | None = None
    if logo is not None:
        logo_bytes = await logo.read()
        logo_filename = logo.filename
        logo_content_type = logo.content_type

    profile = await service.save(
        project_id=project_id,
        primary_color=body.primary_color,
        secondary_color=body.secondary_color,
        accent_color=body.accent_color,
        neutrals=body.neutrals,
        font_heading=body.font_heading,
        font_body=body.font_body,
        logo_bytes=logo_bytes,
        logo_filename=logo_filename,
        logo_content_type=logo_content_type,
    )
    return _to_out(profile, project_id)


@router.post("/{project_id}/brand/preset", response_model=BrandProfileOut)
async def apply_obsidian_preset(
    project_id: uuid.UUID,
    service: BrandService = Depends(get_brand_service),
) -> BrandProfileOut:
    profile = await service.apply_obsidian_preset(project_id)
    return _to_out(profile, project_id)


@router.get("/{project_id}/brand/logo")
async def get_brand_logo(
    project_id: uuid.UUID,
    service: BrandService = Depends(get_brand_service),
) -> Response:
    try:
        data, content_type = await service.fetch_logo(project_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=300"},
    )


@router.post("/{project_id}/brand/palette-suggest", response_model=PaletteSuggestionOut)
async def suggest_palette(
    project_id: uuid.UUID,
    logo: UploadFile = File(...),
    service: BrandService = Depends(get_brand_service),
) -> PaletteSuggestionOut:
    bytes_ = await logo.read()
    suggestions = await service.suggest_palette_from_logo(bytes_)
    return PaletteSuggestionOut(
        suggestions=[PaletteSuggestion(hex=s.hex, population=s.population) for s in suggestions]
    )


# Used by domain Neutrals — re-export so type-checkers don't complain about unused imports.
__all__ = ["Neutrals", "router"]
