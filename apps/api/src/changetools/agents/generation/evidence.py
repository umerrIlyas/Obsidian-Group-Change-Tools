"""Helpers for formatting retrieval hits into prompt context and resolving
LLM-emitted chunk_ids back into typed ``ChunkRef`` objects.
"""

from __future__ import annotations

import uuid

from changetools.domain.chunk import ChunkRef, RetrievalHit

# Per-section retrieval queries. Each runs against the full pgvector index
# so we get the most relevant chunks regardless of source format.
SECTION_QUERIES: dict[str, list[str]] = {
    "executive_summary": [
        "change programme objectives, scope, current status, leadership context",
    ],
    "themes": [
        "recurring themes, patterns, cross-cutting concerns across regions and functions",
        "messaging consistency, communication, sentiment, training adoption",
    ],
    "risks": [
        "programme risks, blockers, issues, escalations, things going wrong",
        "training gaps, adoption shortfalls, regional variance",
    ],
    "stakeholders": [
        "stakeholder concerns, leadership, sponsors, executives, named individuals",
        "regional managers, frontline impact, role changes",
    ],
    "kpis": [
        "key performance indicators, metrics, targets, current values, percentages",
        "digital adoption, training completion, sentiment score, support handling time",
    ],
    "recommendations": [
        "actions, mitigations, recommendations, next steps, decisions to make",
    ],
}


SNIPPET_LEN = 500


def format_chunks_for_prompt(hits: list[RetrievalHit]) -> str:
    """Render hits as a chunk list the LLM can cite from."""
    lines: list[str] = []
    for hit in hits:
        marker = f"[chunk:{hit.chunk.id}]"
        source = f"[{hit.document_kind.upper()} · {hit.document_filename}]"
        text = hit.chunk.text.strip()
        if len(text) > SNIPPET_LEN:
            text = text[:SNIPPET_LEN] + "…"
        lines.append(f"{marker} {source}\n{text}")
    return "\n\n".join(lines)


def resolve_chunk_refs(
    cited_chunk_ids: list[str],
    hits_by_id: dict[uuid.UUID, RetrievalHit],
) -> list[ChunkRef]:
    """Map LLM-emitted UUID strings to typed ChunkRefs.

    Silently drops UUIDs that don't appear in the available evidence pool —
    those would be hallucinated citations and we surface that as a low
    citation_score in metrics rather than failing validation.
    """
    refs: list[ChunkRef] = []
    seen: set[uuid.UUID] = set()
    for raw in cited_chunk_ids:
        try:
            cid = uuid.UUID(raw)
        except (ValueError, AttributeError):
            continue
        if cid in seen:
            continue
        hit = hits_by_id.get(cid)
        if hit is None:
            continue
        seen.add(cid)
        text = hit.chunk.text.strip()
        snippet = text[:300] + "…" if len(text) > 300 else text
        refs.append(
            ChunkRef(
                chunk_id=cid,
                document_id=hit.chunk.document_id,
                document_filename=hit.document_filename,
                snippet=snippet,
            )
        )
    return refs


def hits_index(hits: list[RetrievalHit]) -> dict[uuid.UUID, RetrievalHit]:
    return {h.chunk.id: h for h in hits}


def merge_evidence_pool(
    evidence: dict[str, list[RetrievalHit]],
) -> dict[uuid.UUID, RetrievalHit]:
    """Flatten per-section evidence into one pool for citation lookups.

    Citations may reference chunks retrieved for any section (e.g. the
    executive summary may cite a chunk pulled in for risks). We dedupe by
    chunk_id to keep memory bounded.
    """
    pool: dict[uuid.UUID, RetrievalHit] = {}
    for hits in evidence.values():
        for hit in hits:
            pool.setdefault(hit.chunk.id, hit)
    return pool
