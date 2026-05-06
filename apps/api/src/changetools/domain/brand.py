"""BrandProfile — palette, fonts, logo. Drives both the frontend theme and the
generated deck's branding."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated, TypedDict

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

# Hex colour token — accepts 3 or 6-digit hex, normalises to 6 uppercase digits
HexColor = Annotated[
    str,
    StringConstraints(pattern=r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"),
]


class _ObsidianPreset(TypedDict):
    primary_color: str
    secondary_color: str
    accent_color: str
    neutrals: dict[str, str]
    font_heading: str
    font_body: str


OBSIDIAN_PRESET: _ObsidianPreset = {
    "primary_color": "#0D171E",
    "secondary_color": "#2C343C",
    "accent_color": "#3A8C91",
    "neutrals": {
        "stone": "#6B7280",
        "hairline": "#D9DEE3",
        "fog": "#EEF1F3",
    },
    "font_heading": "Aptos Display",
    "font_body": "Aptos",
}


class Neutrals(BaseModel):
    stone: HexColor = "#6B7280"
    hairline: HexColor = "#D9DEE3"
    fog: HexColor = "#EEF1F3"


class BrandProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    primary_color: HexColor
    secondary_color: HexColor
    accent_color: HexColor
    neutrals: Neutrals
    font_heading: str = Field(..., max_length=200)
    font_body: str = Field(..., max_length=200)
    logo_storage_key: str | None = None
    logo_content_type: str | None = None
    created_at: datetime
    updated_at: datetime


def normalise_hex(value: str) -> str:
    """Return ``#RRGGBB`` upper-case. Expands ``#RGB`` shortcuts."""
    if not re.match(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$", value):
        raise ValueError(f"Invalid hex colour: {value}")
    if len(value) == 4:
        r, g, b = value[1], value[2], value[3]
        return f"#{r}{r}{g}{g}{b}{b}".upper()
    return value.upper()
