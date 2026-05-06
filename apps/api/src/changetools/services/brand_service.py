"""BrandService — palette/font CRUD + logo handling + Obsidian preset."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from changetools.core.errors import NotFoundError, ValidationError
from changetools.core.logging import get_logger
from changetools.domain.brand import (
    OBSIDIAN_PRESET,
    BrandProfile,
    Neutrals,
    normalise_hex,
)
from changetools.infrastructure.branding import (
    DominantColor,
    extract_dominant_colors,
)
from changetools.infrastructure.storage.base import StorageProvider
from changetools.repositories.brand import BrandRepository
from changetools.repositories.projects import ProjectRepository

REPO_ROOT = Path(__file__).resolve().parents[4].parent
OBSIDIAN_LOGO_PATH = REPO_ROOT / "specs" / "Obsidian_Group_Logo.png"

_log = get_logger(__name__)


class BrandService:
    def __init__(
        self,
        *,
        brand: BrandRepository,
        projects: ProjectRepository,
        storage: StorageProvider,
    ) -> None:
        self._brand = brand
        self._projects = projects
        self._storage = storage

    async def get_for_project(self, project_id: uuid.UUID) -> BrandProfile | None:
        return await self._brand.get_for_project(project_id)

    async def save(
        self,
        *,
        project_id: uuid.UUID,
        primary_color: str,
        secondary_color: str,
        accent_color: str,
        neutrals: Neutrals,
        font_heading: str,
        font_body: str,
        logo_bytes: bytes | None = None,
        logo_filename: str | None = None,
        logo_content_type: str | None = None,
    ) -> BrandProfile:
        project = await self._projects.get(project_id)
        if project is None:
            raise NotFoundError(f"Project not found: {project_id}")

        logo_key: str | None = None
        if logo_bytes is not None:
            if not logo_bytes:
                raise ValidationError("Uploaded logo is empty.")
            logo_key = self._logo_key(project_id, logo_filename or "logo.png")
            await self._storage.put(key=logo_key, data=logo_bytes, content_type=logo_content_type)

        return await self._brand.upsert(
            project_id=project_id,
            primary_color=normalise_hex(primary_color),
            secondary_color=normalise_hex(secondary_color),
            accent_color=normalise_hex(accent_color),
            neutrals={
                "stone": normalise_hex(neutrals.stone),
                "hairline": normalise_hex(neutrals.hairline),
                "fog": normalise_hex(neutrals.fog),
            },
            font_heading=font_heading,
            font_body=font_body,
            logo_storage_key=logo_key,
            logo_content_type=logo_content_type if logo_bytes else None,
        )

    async def apply_obsidian_preset(self, project_id: uuid.UUID) -> BrandProfile:
        """Apply the Obsidian Group preset including logo (read from ``specs/``)."""
        logo_bytes: bytes | None = None
        if OBSIDIAN_LOGO_PATH.exists():
            logo_bytes = await asyncio.to_thread(OBSIDIAN_LOGO_PATH.read_bytes)
        else:
            _log.warning("brand.preset.logo_missing", path=str(OBSIDIAN_LOGO_PATH))

        return await self.save(
            project_id=project_id,
            primary_color=OBSIDIAN_PRESET["primary_color"],
            secondary_color=OBSIDIAN_PRESET["secondary_color"],
            accent_color=OBSIDIAN_PRESET["accent_color"],
            neutrals=Neutrals.model_validate(OBSIDIAN_PRESET["neutrals"]),
            font_heading=OBSIDIAN_PRESET["font_heading"],
            font_body=OBSIDIAN_PRESET["font_body"],
            logo_bytes=logo_bytes,
            logo_filename="Obsidian_Group_Logo.png" if logo_bytes else None,
            logo_content_type="image/png" if logo_bytes else None,
        )

    async def fetch_logo(self, project_id: uuid.UUID) -> tuple[bytes, str]:
        profile = await self._brand.get_for_project(project_id)
        if profile is None or not profile.logo_storage_key:
            raise NotFoundError("No logo on this project.")
        data = await self._storage.get(profile.logo_storage_key)
        return data, profile.logo_content_type or "application/octet-stream"

    async def suggest_palette_from_logo(self, image_bytes: bytes) -> list[DominantColor]:
        """Extract palette hints from the uploaded logo. Pure utility — does not persist."""
        return await asyncio.to_thread(extract_dominant_colors, image_bytes)

    @staticmethod
    def _logo_key(project_id: uuid.UUID, filename: str) -> str:
        return f"projects/{project_id}/brand/logo-{uuid.uuid4().hex[:8]}-{filename}"
