"""Docx parser using ``python-docx``.

Walks the document body in order so paragraphs and tables interleave correctly
(important for the assessment's call-notes file, which mixes prose and risk
register tables).
"""

from __future__ import annotations

from typing import Any, BinaryIO

from docx import Document as DocxDocument
from docx.document import Document as _DocxDoc
from docx.oxml.ns import qn
from docx.table import Table as DocxTable
from docx.text.paragraph import Paragraph as DocxParagraph

from changetools.infrastructure.parsing.base import ParsedBlock, ParsedDocument


class DocxParser:
    name = "docx"
    supported_extensions = (".docx",)

    def parse(self, stream: BinaryIO, *, filename: str) -> ParsedDocument:
        document = DocxDocument(stream)
        blocks: list[ParsedBlock] = []
        raw_lines: list[str] = []

        para_index = 0
        table_index = 0
        for child in self._iter_body_children(document):
            if isinstance(child, DocxParagraph):
                text = child.text.strip()
                if not text:
                    continue
                style = (child.style.name or "").lower() if child.style else ""
                kind = "heading" if style.startswith("heading") else "paragraph"
                meta: dict[str, Any] = {
                    "paragraph_index": para_index,
                    "style": style or "normal",
                }
                if kind == "heading":
                    meta["heading_level"] = self._heading_level(style)
                blocks.append(ParsedBlock(kind=kind, text=text, meta=meta))
                raw_lines.append(text)
                para_index += 1
            elif isinstance(child, DocxTable):
                blocks.extend(
                    self._parse_table(child, table_index=table_index, raw_lines=raw_lines)
                )
                table_index += 1

        meta = {
            "paragraph_count": para_index,
            "table_count": table_index,
            "filename": filename,
        }
        return ParsedDocument(
            raw_text="\n".join(raw_lines),
            blocks=blocks,
            meta=meta,
        )

    def _iter_body_children(self, document: _DocxDoc) -> list[DocxParagraph | DocxTable]:
        body = document.element.body
        children: list[DocxParagraph | DocxTable] = []
        for child in body.iterchildren():
            if child.tag == qn("w:p"):
                children.append(DocxParagraph(child, document))
            elif child.tag == qn("w:tbl"):
                children.append(DocxTable(child, document))
        return children

    def _heading_level(self, style: str) -> int:
        # "Heading 1" / "heading 2" / etc.
        digits = "".join(c for c in style if c.isdigit())
        return int(digits) if digits else 1

    def _parse_table(
        self, table: DocxTable, *, table_index: int, raw_lines: list[str]
    ) -> list[ParsedBlock]:
        out: list[ParsedBlock] = []
        rows = table.rows
        if not rows:
            return out

        headers = [cell.text.strip() for cell in rows[0].cells]
        # First row is treated as the header.
        out.append(
            ParsedBlock(
                kind="table_header",
                text=" | ".join(headers),
                meta={"table_index": table_index, "headers": headers},
            )
        )
        raw_lines.append(" | ".join(headers))

        for row_idx, row in enumerate(rows[1:], start=1):
            cells = [cell.text.strip() for cell in row.cells]
            cells_dict = dict(zip(headers, cells, strict=False))
            text = " | ".join(f"{h}: {v}" for h, v in cells_dict.items() if v)
            if not text:
                continue
            out.append(
                ParsedBlock(
                    kind="table_row",
                    text=text,
                    meta={
                        "table_index": table_index,
                        "row_index": row_idx,
                        "headers": headers,
                        "cells": cells_dict,
                    },
                )
            )
            raw_lines.append(text)
        return out
