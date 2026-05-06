"""Brand profile repository — one profile per project, upserted on save."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from changetools.domain.brand import BrandProfile, Neutrals
from changetools.repositories.models.brand import BrandProfileORM


class BrandRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_for_project(self, project_id: uuid.UUID) -> BrandProfile | None:
        result = await self._session.execute(
            select(BrandProfileORM).where(BrandProfileORM.project_id == project_id)
        )
        row = result.scalar_one_or_none()
        return self._to_domain(row) if row else None

    async def upsert(
        self,
        *,
        project_id: uuid.UUID,
        primary_color: str,
        secondary_color: str,
        accent_color: str,
        neutrals: dict[str, str],
        font_heading: str,
        font_body: str,
        logo_storage_key: str | None,
        logo_content_type: str | None,
    ) -> BrandProfile:
        result = await self._session.execute(
            select(BrandProfileORM).where(BrandProfileORM.project_id == project_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            row = BrandProfileORM(project_id=project_id)
            self._session.add(row)

        row.primary_color = primary_color
        row.secondary_color = secondary_color
        row.accent_color = accent_color
        row.neutrals = neutrals
        row.font_heading = font_heading
        row.font_body = font_body
        # Preserve existing logo when caller passes ``None`` for both fields.
        if logo_storage_key is not None:
            row.logo_storage_key = logo_storage_key
            row.logo_content_type = logo_content_type

        await self._session.flush()
        await self._session.refresh(row)
        return self._to_domain(row)

    @staticmethod
    def _to_domain(row: BrandProfileORM) -> BrandProfile:
        neutrals_data: dict[str, Any] = row.neutrals or {}
        return BrandProfile(
            id=row.id,
            project_id=row.project_id,
            primary_color=row.primary_color,
            secondary_color=row.secondary_color,
            accent_color=row.accent_color,
            neutrals=Neutrals.model_validate(neutrals_data) if neutrals_data else Neutrals(),
            font_heading=row.font_heading,
            font_body=row.font_body,
            logo_storage_key=row.logo_storage_key,
            logo_content_type=row.logo_content_type,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
