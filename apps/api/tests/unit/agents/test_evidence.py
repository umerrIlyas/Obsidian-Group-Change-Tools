"""Tests for the chunk-citation resolver."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from changetools.agents.generation.evidence import (
    format_chunks_for_prompt,
    hits_index,
    merge_evidence_pool,
    resolve_chunk_refs,
)
from changetools.domain.chunk import Chunk, RetrievalHit


def _hit(text: str, kind: str = "docx", filename: str = "notes.docx") -> RetrievalHit:
    chunk_id = uuid.uuid4()
    chunk = Chunk(
        id=chunk_id,
        document_id=uuid.uuid4(),
        ordinal=0,
        text=text,
        meta={},
        embedding=None,
        score=0.9,
        created_at=datetime.now(UTC),
    )
    return RetrievalHit(chunk=chunk, document_filename=filename, document_kind=kind, score=0.9)


def test_resolve_chunk_refs_drops_unknown_uuids():
    hit = _hit("Sana Patel said the rollout was rushed.")
    pool = hits_index([hit])
    refs = resolve_chunk_refs([str(hit.chunk.id), str(uuid.uuid4()), "not-a-uuid"], pool)
    assert len(refs) == 1
    assert refs[0].chunk_id == hit.chunk.id
    assert refs[0].document_filename == "notes.docx"
    assert refs[0].snippet is not None


def test_resolve_chunk_refs_dedupes():
    hit = _hit("once")
    pool = hits_index([hit])
    refs = resolve_chunk_refs([str(hit.chunk.id)] * 3, pool)
    assert len(refs) == 1


def test_format_chunks_includes_marker_and_kind():
    hit = _hit("Digital adoption at 42%.", kind="xlsx", filename="data.xlsx")
    block = format_chunks_for_prompt([hit])
    assert f"[chunk:{hit.chunk.id}]" in block
    assert "[XLSX · data.xlsx]" in block
    assert "Digital adoption at 42%." in block


def test_format_chunks_truncates_long_text():
    long_text = "x" * 1000
    hit = _hit(long_text)
    block = format_chunks_for_prompt([hit])
    assert "…" in block
    # Truncated body should be shorter than the original.
    assert len(block) < 1100


def test_merge_evidence_pool_dedupes_across_sections():
    h1 = _hit("a")
    h2 = _hit("b")
    pool = merge_evidence_pool({"risks": [h1, h2], "kpis": [h1]})
    assert set(pool.keys()) == {h1.chunk.id, h2.chunk.id}
