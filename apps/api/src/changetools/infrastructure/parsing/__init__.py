"""Document parsers — convert binary uploads into typed parsed blocks.

Each parser returns a ``ParsedDocument``: the raw text (for fulltext storage),
a list of typed blocks (for chunking), and source-level metadata (page/sheet
counts, table catalogues, etc.).
"""

from changetools.infrastructure.parsing.base import (
    BlockKind,
    ParsedBlock,
    ParsedDocument,
    Parser,
)
from changetools.infrastructure.parsing.docx_parser import DocxParser
from changetools.infrastructure.parsing.factory import parse_document
from changetools.infrastructure.parsing.xlsx_parser import XlsxParser

__all__ = [
    "BlockKind",
    "DocxParser",
    "ParsedBlock",
    "ParsedDocument",
    "Parser",
    "XlsxParser",
    "parse_document",
]
