"""Map LLM-emitted ``cited_chunk_ids`` back to typed ``ChunkRef`` objects
and compute a per-brief citation score (% of items with valid citations).

A heavier "LLM-as-judge" pass would double-check that each chunk actually
supports its claim. For MVP we trust the structural grounding (chunk_id
present and resolves to a real chunk) and downgrade ``confidence`` for
items that emitted no resolvable citations.
"""

from __future__ import annotations

from typing import Any

from changetools.agents.generation.evidence import (
    merge_evidence_pool,
    resolve_chunk_refs,
)
from changetools.agents.generation.state import GenerationState


def _cite_one(item: dict, pool: dict) -> dict:
    """Return a copy of ``item`` with ``evidence`` populated and confidence
    downgraded if no citations resolve."""
    raw_ids = item.get("cited_chunk_ids", []) or []
    refs = resolve_chunk_refs(raw_ids, pool)
    out = {**item}
    out["evidence"] = [r.model_dump(mode="json") for r in refs]
    if not refs:
        out["confidence"] = "low"
    out.pop("cited_chunk_ids", None)
    return out


async def cite_evidence_node(state: GenerationState) -> dict:
    pool = merge_evidence_pool(state.evidence)
    drafts = state.drafts
    grounded: dict[str, Any] = {}

    cited_total = 0
    grounded_total = 0

    if "executive_summary" in drafts:
        grounded["executive_summary"] = _cite_one(drafts["executive_summary"], pool)
        cited_total += 1
        if grounded["executive_summary"]["evidence"]:
            grounded_total += 1

    for section in ("themes", "risks", "stakeholders", "kpis", "recommendations"):
        items = (drafts.get(section) or {}).get("items") or []
        cited_items = [_cite_one(it, pool) for it in items]
        grounded[section] = cited_items
        for it in cited_items:
            cited_total += 1
            if it["evidence"]:
                grounded_total += 1

    citation_rate = round(grounded_total / cited_total, 2) if cited_total else 0.0

    return {
        "drafts": {**state.drafts, "_grounded": grounded},
        "metrics": {
            **state.metrics,
            "items_total": cited_total,
            "items_grounded": grounded_total,
            "citation_rate": citation_rate,
        },
    }
