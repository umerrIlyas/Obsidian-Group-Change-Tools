"""Parser selection by filename / content type."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import BinaryIO

from changetools.core.errors import ValidationError
from changetools.infrastructure.parsing.base import ParsedDocument, Parser
from changetools.infrastructure.parsing.docx_parser import DocxParser
from changetools.infrastructure.parsing.xlsx_parser import XlsxParser

_PARSERS: list[Parser] = [DocxParser(), XlsxParser()]


def parse_document(stream: BinaryIO, *, filename: str) -> ParsedDocument:
    """Pick the right parser for ``filename`` and run it. Raises on unsupported types."""
    suffix = PurePosixPath(filename).suffix.lower()
    for parser in _PARSERS:
        if suffix in parser.supported_extensions:
            return parser.parse(stream, filename=filename)
    raise ValidationError(
        f"Unsupported file extension: {suffix!r}. Supported: "
        + ", ".join(sorted({ext for p in _PARSERS for ext in p.supported_extensions}))
    )
