"""Convert ``ParsedDocument`` blocks into chunk seeds ready for embedding.

Strategy:
  - **Spreadsheet rows** stay 1 row = 1 chunk. Each row's text already carries the
    sheet/table prefix and ``"header: value"`` pairs, so it's self-describing.
  - **Prose** (docx paragraphs / list items) is grouped into windows of up to
    ``max_tokens`` words, with the most recent heading prepended for context so a
    chunk retrieved out of order still makes sense.
  - **Tables embedded in prose docs** still get 1 row = 1 chunk, with the heading
    that introduced the table prepended.

Token counting uses a fast word-count heuristic — exact tokenisation is not
worth the dependency for chunking decisions at this scale.
"""

from __future__ import annotations

from typing import Any, NamedTuple

from changetools.domain.document import DocumentKind
from changetools.infrastructure.parsing.base import ParsedBlock, ParsedDocument

DEFAULT_MAX_TOKENS = 350


class ChunkSeed(NamedTuple):
    text: str
    meta: dict[str, Any]


class ChunkingService:
    def __init__(self, *, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        self._max_tokens = max_tokens

    def chunk(
        self,
        parsed: ParsedDocument,
        document_kind: DocumentKind,
    ) -> list[ChunkSeed]:
        if document_kind == "xlsx":
            return self._chunk_table_rows(parsed)
        return self._chunk_prose(parsed)

    # --- strategies ---

    @staticmethod
    def _chunk_table_rows(parsed: ParsedDocument) -> list[ChunkSeed]:
        seeds: list[ChunkSeed] = []
        for block in parsed.blocks:
            if block.kind != "table_row":
                continue
            seeds.append(
                ChunkSeed(
                    text=block.text,
                    meta={**block.meta, "block_kind": "table_row"},
                )
            )
        return seeds

    def _chunk_prose(self, parsed: ParsedDocument) -> list[ChunkSeed]:
        seeds: list[ChunkSeed] = []
        buffer: list[ParsedBlock] = []
        buffer_tokens = 0
        current_heading: str | None = None
        first_para_index: int | None = None

        def flush() -> None:
            nonlocal buffer_tokens, first_para_index
            if not buffer:
                return
            parts: list[str] = []
            if current_heading:
                parts.append(f"# {current_heading}")
            parts.extend(b.text for b in buffer)
            seeds.append(
                ChunkSeed(
                    text="\n\n".join(parts),
                    meta={
                        "heading": current_heading,
                        "block_kinds": [b.kind for b in buffer],
                        "first_paragraph_index": first_para_index,
                        "block_count": len(buffer),
                    },
                )
            )
            buffer.clear()
            buffer_tokens = 0
            first_para_index = None

        for block in parsed.blocks:
            if block.kind == "heading":
                flush()
                current_heading = block.text
                continue
            if block.kind == "table_header":
                # Headers carry no retrievable signal on their own; we already include
                # them inside each row's self-describing text.
                continue
            if block.kind == "table_row":
                flush()
                seeds.append(
                    ChunkSeed(
                        text=(
                            f"# {current_heading}\n\n{block.text}"
                            if current_heading
                            else block.text
                        ),
                        meta={
                            **block.meta,
                            "block_kind": "table_row",
                            "heading": current_heading,
                        },
                    )
                )
                continue

            block_tokens = self._estimate_tokens(block.text)
            if buffer and buffer_tokens + block_tokens > self._max_tokens:
                flush()
            buffer.append(block)
            buffer_tokens += block_tokens
            if first_para_index is None:
                first_para_index = block.meta.get("paragraph_index")

        flush()
        return seeds

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        # Cheap proxy for token count — adequate for chunking decisions.
        words = max(1, len(text.split()))
        return int(words * 1.3)
