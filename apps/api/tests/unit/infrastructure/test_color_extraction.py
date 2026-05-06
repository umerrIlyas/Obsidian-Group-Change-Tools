"""Pillow-based dominant-colour extraction."""

from __future__ import annotations

import io

from PIL import Image

from changetools.infrastructure.branding.color_extraction import (
    DominantColor,
    extract_dominant_colors,
)


def _png_bytes(color: tuple[int, int, int], size: int = 32) -> bytes:
    img = Image.new("RGB", (size, size), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_uniform_image_returns_single_dominant_color() -> None:
    palette = extract_dominant_colors(_png_bytes((58, 140, 145)))  # Obsidian Teal
    assert palette
    assert palette[0].hex == "#3A8C91"
    assert palette[0].population > 0


def test_two_color_image_returns_both() -> None:
    img = Image.new("RGB", (40, 20))
    img.paste(Image.new("RGB", (20, 20), (13, 23, 30)), (0, 0))
    img.paste(Image.new("RGB", (20, 20), (255, 255, 255)), (20, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    palette = extract_dominant_colors(buf.getvalue())
    hexes = {c.hex for c in palette}
    assert "#0D171E" in hexes
    assert "#FFFFFF" in hexes


def test_empty_input_returns_empty() -> None:
    assert extract_dominant_colors(b"") == []


def test_returns_dataclass_instances() -> None:
    palette = extract_dominant_colors(_png_bytes((44, 52, 60)))
    assert all(isinstance(c, DominantColor) for c in palette)
