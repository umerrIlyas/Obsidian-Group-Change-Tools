"""ChunkingService strategies for prose vs spreadsheet rows."""

from __future__ import annotations

from changetools.infrastructure.parsing.base import ParsedBlock, ParsedDocument
from changetools.services.chunking_service import ChunkingService


def _doc(*blocks: ParsedBlock) -> ParsedDocument:
    return ParsedDocument(
        raw_text="\n".join(b.text for b in blocks),
        blocks=list(blocks),
    )


def test_xlsx_strategy_one_chunk_per_row() -> None:
    parsed = _doc(
        ParsedBlock(kind="table_header", text="hdr", meta={"table": "T"}),
        ParsedBlock(kind="table_row", text="row 1", meta={"table": "T", "row_index": 1}),
        ParsedBlock(kind="table_row", text="row 2", meta={"table": "T", "row_index": 2}),
    )
    seeds = ChunkingService().chunk(parsed, "xlsx")
    assert len(seeds) == 2
    assert seeds[0].text == "row 1"
    assert seeds[1].meta["row_index"] == 2


def test_prose_strategy_groups_paragraphs_under_max_tokens() -> None:
    blocks = [
        ParsedBlock(kind="heading", text="Section A", meta={"heading_level": 1}),
        *(
            ParsedBlock(
                kind="paragraph",
                text=" ".join(["word"] * 30),
                meta={"paragraph_index": i},
            )
            for i in range(20)
        ),
    ]
    seeds = ChunkingService(max_tokens=200).chunk(_doc(*blocks), "docx")
    assert len(seeds) > 1  # multiple windows
    # Heading is prepended to every chunk for context.
    assert all(s.text.startswith("# Section A") for s in seeds)
    # Each chunk's meta carries the heading.
    assert all(s.meta["heading"] == "Section A" for s in seeds)


def test_prose_strategy_emits_table_rows_individually() -> None:
    parsed = _doc(
        ParsedBlock(kind="heading", text="Risk register", meta={"heading_level": 2}),
        ParsedBlock(kind="paragraph", text="A short intro paragraph.", meta={"paragraph_index": 0}),
        ParsedBlock(kind="table_header", text="ID | Risk", meta={"table_index": 0}),
        ParsedBlock(
            kind="table_row",
            text="ID: R-01 | Risk: middle management resistance",
            meta={"table_index": 0, "row_index": 1},
        ),
        ParsedBlock(
            kind="table_row",
            text="ID: R-02 | Risk: job security concerns",
            meta={"table_index": 0, "row_index": 2},
        ),
    )
    seeds = ChunkingService().chunk(parsed, "docx")
    table_seeds = [s for s in seeds if s.meta.get("block_kind") == "table_row"]
    assert len(table_seeds) == 2
    assert all("Risk register" in s.text for s in table_seeds)


def test_skips_empty_input() -> None:
    seeds = ChunkingService().chunk(_doc(), "docx")
    assert seeds == []
