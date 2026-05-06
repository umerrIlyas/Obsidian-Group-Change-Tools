"""Smoke tests for the BrandedDeckRenderer.

We don't pixel-compare slides — we just confirm the renderer produces a valid
.pptx file structure with the expected slide count for a typical brief.
"""

from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

import pytest
from pptx import Presentation

from changetools.domain.brand import BrandProfile, Neutrals
from changetools.domain.brief import (
    KPI,
    Brief,
    BriefContent,
    Conflict,
    ExecutiveSummary,
    Recommendation,
    Risk,
    Stakeholder,
    Theme,
)
from changetools.domain.chunk import ChunkRef
from changetools.infrastructure.rendering.pptx_renderer import (
    BrandedDeckRenderer,
    _hex_to_rgb,
    _truncate,
)


def _ref(filename: str = "notes.docx") -> ChunkRef:
    return ChunkRef(
        chunk_id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        document_filename=filename,
        snippet="excerpt",
    )


def _brand() -> BrandProfile:
    return BrandProfile(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        primary_color="#0D171E",
        secondary_color="#2C343C",
        accent_color="#3A8C91",
        neutrals=Neutrals(stone="#6B7280", hairline="#D9DEE3", fog="#EEF1F3"),
        font_heading="Aptos Display",
        font_body="Aptos",
        logo_storage_key=None,
        logo_content_type=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _full_brief() -> Brief:
    content = BriefContent(
        executive_summary=ExecutiveSummary(
            headline="Programme is on track but adoption lags",
            body="Two-thirds of regions hit milestones; LATAM is at risk.",
            evidence=[_ref()],
            confidence="medium",
        ),
        themes=[
            Theme(title="Adoption variance", description="LATAM lagging.", evidence=[_ref()]),
            Theme(title="Messaging drift", description="Five separate scripts.", evidence=[_ref()]),
        ],
        risks=[
            Risk(
                risk_id="R-01",
                title="Regional adoption gap",
                description="LATAM 28pp below target.",
                severity="high",
                owner="Sana Patel",
                mitigation="Field comms refresh.",
                evidence=[_ref("data.xlsx")],
            ),
        ],
        stakeholders=[
            Stakeholder(
                name="Elena Brooks",
                role="VP Comms",
                concern="Messaging drift",
                sentiment="concerned",
                evidence=[_ref()],
            ),
        ],
        kpis=[
            KPI(
                name="Digital adoption",
                current_value="42%",
                target_value="75%",
                gap="33pp behind",
                trend="up since Q2",
                evidence=[_ref("data.xlsx")],
            ),
        ],
        recommendations=[
            Recommendation(
                title="Launch regional change champion network",
                description="Empower local champions to land messaging.",
                priority="P1",
                addresses_risks=["R-01"],
                evidence=[_ref()],
            ),
        ],
        conflicts=[
            Conflict(
                topic="Training completion target",
                position_a="Stated as 80% in call notes",
                position_b="Recorded as 90% in data pack",
                sources_a=[_ref()],
                sources_b=[_ref("data.xlsx")],
                suggested_resolution="Prefer data pack.",
            ),
        ],
    )
    return Brief(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        version=1,
        status="ready",
        model_name="llama-3.3-70b-versatile",
        provider="groq",
        content=content,
        metrics={"items_total": 7, "items_grounded": 7, "citation_rate": 1.0},
        error=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def test_render_produces_valid_pptx_with_expected_slide_count():
    renderer = BrandedDeckRenderer(brand=_brand(), project_name="Obsidian", logo_bytes=None)
    pptx_bytes, count = renderer.render(_full_brief())

    # Title + exec summary + themes + KPIs + risks + stakeholders + recs + conflicts.
    assert count == 8

    prs = Presentation(io.BytesIO(pptx_bytes))
    assert len(prs.slides) == 8


def test_render_skips_empty_sections():
    minimal = Brief(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        version=1,
        status="ready",
        model_name=None,
        provider=None,
        content=BriefContent(
            executive_summary=ExecutiveSummary(
                headline="Brief", body="Body", evidence=[], confidence="low"
            ),
        ),
        metrics={},
        error=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    renderer = BrandedDeckRenderer(brand=None, project_name="Test", logo_bytes=None)
    _, count = renderer.render(minimal)
    # Only title + exec summary should render.
    assert count == 2


def test_hex_to_rgb_rejects_bad_input():
    with pytest.raises(ValueError, match="Bad hex"):
        _hex_to_rgb("notahex")


def test_truncate_keeps_short_strings():
    assert _truncate("short", 100) == "short"
    assert _truncate("x" * 200, 50).endswith("…")
    assert len(_truncate("x" * 200, 50)) == 50
