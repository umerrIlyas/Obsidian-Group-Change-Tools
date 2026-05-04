"""Parser tests against the actual Obsidian Group fixture documents."""

from __future__ import annotations

from pathlib import Path

import pytest

from changetools.infrastructure.parsing import DocxParser, XlsxParser, parse_document

REPO_ROOT = Path(__file__).resolve().parents[4].parent
SPECS = REPO_ROOT / "specs"
DOCX_FIXTURE = SPECS / "Obsidian_Group_AI_Call_Notes.docx"
XLSX_FIXTURE = SPECS / "Obsidian_Group_Change_Data_Pack.xlsx"


@pytest.fixture(scope="session")
def docx_bytes() -> bytes:
    if not DOCX_FIXTURE.exists():
        pytest.skip(f"Fixture not present: {DOCX_FIXTURE}")
    return DOCX_FIXTURE.read_bytes()


@pytest.fixture(scope="session")
def xlsx_bytes() -> bytes:
    if not XLSX_FIXTURE.exists():
        pytest.skip(f"Fixture not present: {XLSX_FIXTURE}")
    return XLSX_FIXTURE.read_bytes()


# --- Docx ---


def test_docx_parser_extracts_paragraphs_and_tables(docx_bytes: bytes) -> None:
    import io

    parsed = DocxParser().parse(io.BytesIO(docx_bytes), filename="call_notes.docx")
    assert parsed.meta["paragraph_count"] > 20
    assert parsed.meta["table_count"] >= 2  # the file has theme + risk register tables
    assert "Amelia Hart" in parsed.raw_text  # CEO is mentioned
    assert "regional manager resistance" in parsed.raw_text.lower()
    # At least one heading-style block should be detected.
    assert any(b.kind == "heading" for b in parsed.blocks)
    # At least one table_row carries cells dict.
    table_rows = [b for b in parsed.blocks if b.kind == "table_row"]
    assert table_rows
    assert isinstance(table_rows[0].meta["cells"], dict)


def test_docx_parser_via_factory(docx_bytes: bytes) -> None:
    import io

    parsed = parse_document(io.BytesIO(docx_bytes), filename="call_notes.docx")
    assert parsed.blocks


# --- Xlsx ---


def test_xlsx_parser_picks_up_named_tables(xlsx_bytes: bytes) -> None:
    import io

    parsed = XlsxParser().parse(io.BytesIO(xlsx_bytes), filename="data_pack.xlsx")
    table_names = {t["table"] for t in parsed.meta["tables"]}
    # The data pack defines five named tables.
    assert {
        "KPITracker",
        "RiskRegister",
        "StakeholderMap",
        "CommsCalendar",
        "DataDictionary",
    }.issubset(table_names)

    kpi_rows = [
        b for b in parsed.blocks if b.kind == "table_row" and b.meta.get("table") == "KPITracker"
    ]
    assert len(kpi_rows) > 0
    headers = kpi_rows[0].meta["headers"]
    assert "Digital Workflow Adoption %" in headers
    assert "Region" in headers


def test_xlsx_parser_emits_table_headers(xlsx_bytes: bytes) -> None:
    import io

    parsed = XlsxParser().parse(io.BytesIO(xlsx_bytes), filename="data_pack.xlsx")
    headers = [b for b in parsed.blocks if b.kind == "table_header"]
    assert len(headers) >= 5  # one per named table


def test_xlsx_row_text_is_self_describing(xlsx_bytes: bytes) -> None:
    import io

    parsed = XlsxParser().parse(io.BytesIO(xlsx_bytes), filename="data_pack.xlsx")
    risk_rows = [
        b for b in parsed.blocks if b.kind == "table_row" and b.meta.get("table") == "RiskRegister"
    ]
    assert risk_rows
    sample = risk_rows[0].text
    # Format prepends a [sheet · table] prefix and then "header: value | ..."
    assert sample.startswith("[Risk Register · RiskRegister]")
    assert "Risk ID:" in sample or "Risk:" in sample
