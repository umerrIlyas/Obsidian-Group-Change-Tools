"""Brand DTOs."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from changetools.domain.brand import HexColor, Neutrals


class BrandProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    primary_color: HexColor
    secondary_color: HexColor
    accent_color: HexColor
    neutrals: Neutrals
    font_heading: str
    font_body: str
    logo_url: str | None = None
    created_at: datetime
    updated_at: datetime


class UpdateBrandIn(BaseModel):
    primary_color: HexColor
    secondary_color: HexColor
    accent_color: HexColor
    neutrals: Neutrals
    font_heading: str = Field(..., min_length=1, max_length=200)
    font_body: str = Field(..., min_length=1, max_length=200)


class PaletteSuggestion(BaseModel):
    hex: HexColor
    population: int


class PaletteSuggestionOut(BaseModel):
    suggestions: list[PaletteSuggestion]
