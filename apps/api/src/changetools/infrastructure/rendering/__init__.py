"""Deck rendering: python-pptx → .pptx, LibreOffice → .pdf preview."""

from changetools.infrastructure.rendering.pdf_converter import (
    LibreOfficeMissingError,
    pptx_to_pdf,
)
from changetools.infrastructure.rendering.pptx_renderer import BrandedDeckRenderer

__all__ = [
    "BrandedDeckRenderer",
    "LibreOfficeMissingError",
    "pptx_to_pdf",
]
