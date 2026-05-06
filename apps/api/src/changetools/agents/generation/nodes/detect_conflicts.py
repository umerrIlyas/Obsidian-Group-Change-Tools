"""Detect disagreements between call-notes and data-pack chunks.

We split the evidence pool by ``document_kind`` (call_notes vs data_pack /
other) and ask the LLM to surface specific conflicts. If the splits don't
both have content we skip the call entirely — no conflicts are possible.
"""

from __future__ import annotations

from collections import defaultdict

from changetools.agents.generation.evidence import (
    format_chunks_for_prompt,
    merge_evidence_pool,
    resolve_chunk_refs,
)
from changetools.agents.generation.schemas import DraftConflicts
from changetools.agents.generation.state import GenerationState
from changetools.agents.prompts.sections import CONFLICT_DETECTION, SYSTEM
from changetools.infrastructure.llm.base import LLMProvider
from changetools.infrastructure.llm.structured import invoke_structured

# Document kinds we treat as "call notes" vs "data pack". Anything that is
# clearly tabular is data pack; everything else collapses to call notes.
DATA_PACK_KINDS = {"data_pack", "xlsx", "csv", "spreadsheet"}


def make_detect_conflicts_node(llm: LLMProvider):
    async def detect_conflicts_node(state: GenerationState) -> dict:
        pool = merge_evidence_pool(state.evidence)
        if not pool:
            return {"drafts": {**state.drafts, "_conflicts": []}}

        buckets: dict[str, list] = defaultdict(list)
        for hit in pool.values():
            kind = (hit.document_kind or "").lower()
            bucket = "data" if kind in DATA_PACK_KINDS else "notes"
            buckets[bucket].append(hit)

        if not buckets.get("notes") or not buckets.get("data"):
            # Need both pools to find conflicts; skip otherwise.
            return {"drafts": {**state.drafts, "_conflicts": []}}

        notes_block = format_chunks_for_prompt(buckets["notes"][:12])
        data_block = format_chunks_for_prompt(buckets["data"][:12])

        chat_model = llm.chat_model(temperature=0.1, max_tokens=1600)

        user_prompt = (
            f"{CONFLICT_DETECTION}\n\n"
            f"## Call notes pool\n{notes_block}\n\n"
            f"## Data pack pool\n{data_block}\n\n"
            "Return JSON only."
        )

        try:
            parsed = await invoke_structured(
                chat_model,
                schema=DraftConflicts,
                system=SYSTEM,
                user=user_prompt,
            )
        except Exception:
            # Conflict detection is non-fatal — empty list is a legitimate result.
            return {"drafts": {**state.drafts, "_conflicts": []}}

        # Map UUID strings back to ChunkRefs and drop conflicts with no
        # resolvable evidence on either side (they're hallucinations).
        out = []
        for c in parsed.items:
            sources_a = resolve_chunk_refs(c.sources_a_chunk_ids, pool)
            sources_b = resolve_chunk_refs(c.sources_b_chunk_ids, pool)
            if not sources_a or not sources_b:
                continue
            out.append(
                {
                    "topic": c.topic,
                    "position_a": c.position_a,
                    "position_b": c.position_b,
                    "sources_a": [r.model_dump(mode="json") for r in sources_a],
                    "sources_b": [r.model_dump(mode="json") for r in sources_b],
                    "suggested_resolution": c.suggested_resolution,
                }
            )

        return {
            "drafts": {**state.drafts, "_conflicts": out},
            "metrics": {**state.metrics, "conflicts_detected": len(out)},
        }

    return detect_conflicts_node


detect_conflicts_node = make_detect_conflicts_node
