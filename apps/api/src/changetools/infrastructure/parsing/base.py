"""Parser Protocol + parsed-block types."""

from __future__ import annotations

from typing import Any, BinaryIO, Literal, Protocol

from pydantic import BaseModel, Field

BlockKind = Literal[
    "heading",
    "paragraph",
    "list_item",
    "table_header",
    "table_row",
    "table_cell",
]


class ParsedBlock(BaseModel):
    """One semantic unit produced by a parser.

    Source-specific context (page, sheet, table, row) lives in ``meta`` so
    chunking and citation logic can stay parser-agnostic.
    """

    kind: BlockKind
    text: str
    meta: dict[str, Any] = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    """Complete parser output for a single uploaded document."""

    raw_text: str
    blocks: list[ParsedBlock]
    meta: dict[str, Any] = Field(default_factory=dict)


class Parser(Protocol):
    """Adapter that turns a binary stream into a ``ParsedDocument``."""

    name: str
    supported_extensions: tuple[str, ...]

    def parse(self, stream: BinaryIO, *, filename: str) -> ParsedDocument: ...
