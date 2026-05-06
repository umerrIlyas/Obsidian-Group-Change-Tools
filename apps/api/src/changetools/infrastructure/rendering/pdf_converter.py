"""LibreOffice subprocess wrapper that turns a .pptx into a preview .pdf.

LibreOffice is the cheapest path to fidelity-preserving PowerPoint→PDF
without paying for the Aspose / Cloudmersive equivalents. The price is a
~1.5GB image in the prod container; we install it in the Render Dockerfile.

In dev, LibreOffice is often missing. ``pptx_to_pdf`` raises
``LibreOfficeMissingError`` in that case so callers can decide to skip the
PDF and serve only the .pptx.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path

from changetools.core.errors import ChangeToolsError, ProviderError

# LibreOffice ships as ``libreoffice`` on apt-based images and ``soffice`` on
# many macOS installs (and via the brew cask). We try both.
_BINARIES = ("soffice", "libreoffice")


class LibreOfficeMissingError(ChangeToolsError):
    """Raised when neither ``soffice`` nor ``libreoffice`` is on PATH."""

    status_code = 503
    code = "libreoffice_missing"


def find_libreoffice() -> str | None:
    for name in _BINARIES:
        path = shutil.which(name)
        if path:
            return path
    return None


async def pptx_to_pdf(pptx_bytes: bytes, *, timeout: float = 90.0) -> bytes:
    """Convert .pptx bytes to .pdf bytes via LibreOffice headless.

    Synchronous LibreOffice spawn happens in a thread to avoid blocking the
    event loop.
    """
    binary = find_libreoffice()
    if binary is None:
        raise LibreOfficeMissingError(
            "LibreOffice not found on PATH (tried: soffice, libreoffice). "
            "PDF preview is unavailable in this environment.",
        )

    return await asyncio.to_thread(_run_conversion, binary, pptx_bytes, timeout)


def _run_conversion(binary: str, pptx_bytes: bytes, timeout: float) -> bytes:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        pptx_path = tmp_path / "deck.pptx"
        pptx_path.write_bytes(pptx_bytes)

        # ``--convert-to pdf`` writes a sibling .pdf in --outdir.
        proc = subprocess.run(
            [
                binary,
                "--headless",
                "--norestore",
                "--nolockcheck",
                "--convert-to",
                "pdf",
                "--outdir",
                str(tmp_path),
                str(pptx_path),
            ],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        pdf_path = tmp_path / "deck.pdf"
        if not pdf_path.exists():
            stderr = proc.stderr.decode("utf-8", errors="replace")[:500]
            raise ProviderError(
                f"LibreOffice did not produce a PDF: {stderr or 'no stderr'}",
                code="libreoffice_failed",
            )
        return pdf_path.read_bytes()
