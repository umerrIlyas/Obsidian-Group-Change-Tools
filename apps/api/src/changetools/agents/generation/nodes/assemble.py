"""Assemble grounded section drafts + conflicts into a final BriefContent."""

from __future__ import annotations

from changetools.agents.generation.state import GenerationState
from changetools.domain.brief import (
    KPI,
    BriefContent,
    Conflict,
    ExecutiveSummary,
    Recommendation,
    Risk,
    Stakeholder,
    Theme,
)


async def assemble_node(state: GenerationState) -> dict:
    grounded = state.drafts.get("_grounded") or {}
    conflicts_raw = state.drafts.get("_conflicts") or []

    exec_summary = ExecutiveSummary.model_validate(
        grounded.get("executive_summary")
        or {"headline": "Brief unavailable", "body": "(no draft produced)"}
    )

    content = BriefContent(
        executive_summary=exec_summary,
        themes=[Theme.model_validate(t) for t in grounded.get("themes") or []],
        risks=[Risk.model_validate(r) for r in grounded.get("risks") or []],
        stakeholders=[Stakeholder.model_validate(s) for s in grounded.get("stakeholders") or []],
        kpis=[KPI.model_validate(k) for k in grounded.get("kpis") or []],
        recommendations=[
            Recommendation.model_validate(r) for r in grounded.get("recommendations") or []
        ],
        conflicts=[Conflict.model_validate(c) for c in conflicts_raw],
    )

    return {"content": content}
