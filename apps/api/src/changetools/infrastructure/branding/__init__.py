"""Brand-related image utilities (palette extraction, logo handling)."""

from changetools.infrastructure.branding.color_extraction import (
    DominantColor,
    extract_dominant_colors,
)

__all__ = ["DominantColor", "extract_dominant_colors"]
