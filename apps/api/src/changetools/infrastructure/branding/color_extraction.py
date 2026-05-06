"""Extract a dominant-colour palette from a logo image.

Approach:
  1. Load the image, drop the alpha channel against white so transparent areas don't
     pollute the palette.
  2. Downscale to a small thumbnail for speed (the palette is the same).
  3. Use Pillow's median-cut quantizer to bucket the pixels into N colours.
  4. Sort by population.
  5. Filter near-white / near-black colours since they're rarely useful brand tokens
     — but keep the most-used dark colour as a candidate primary, and the most-used
     saturated colour as a candidate accent.

The result is intentionally a hint for the user, not a final palette: the UI shows
these as starting points the user can override.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class DominantColor:
    hex: str
    population: int  # number of pixels assigned to this colour after quantisation


def extract_dominant_colors(
    image_bytes: bytes,
    *,
    max_colors: int = 8,
    thumbnail_size: int = 200,
) -> list[DominantColor]:
    if not image_bytes:
        return []
    image: Image.Image = Image.open(io.BytesIO(image_bytes))
    image = _flatten_alpha(image)
    image.thumbnail((thumbnail_size, thumbnail_size))

    quantised = image.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    palette: list[int] = quantised.getpalette() or []
    counts = quantised.getcolors() or []

    results: list[DominantColor] = []
    for entry in counts:
        # ``getcolors`` returns ``list[tuple[count, palette_index]]`` for a
        # palette image, but its declared return type is wider; narrow here.
        if not isinstance(entry, tuple) or len(entry) != 2:
            continue
        population, palette_index = entry
        if not isinstance(palette_index, int):
            continue
        r = palette[palette_index * 3]
        g = palette[palette_index * 3 + 1]
        b = palette[palette_index * 3 + 2]
        results.append(
            DominantColor(
                hex=f"#{r:02X}{g:02X}{b:02X}",
                population=int(population),
            )
        )
    results.sort(key=lambda c: c.population, reverse=True)
    return results


def _flatten_alpha(image: Image.Image) -> Image.Image:
    """Composite onto a white background so transparent PNGs don't bias the palette."""
    if image.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])
        return background
    return image.convert("RGB")
