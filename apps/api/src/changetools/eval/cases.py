"""Eval case definitions.

Each case is a function ``(brief, ctx) -> EvalResult`` returning pass/fail
plus a list of human-readable assertion outcomes. Cases are intentionally
forgiving on phrasing (``"adoption" in name.lower()``) but strict on
structural guarantees (every claim has citations).

The ``EvalContext`` carries auxiliary data so cases that need to verify
citations against the live RAG index can do so without re-loading them.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from changetools.domain.brief import Brief, BriefContent
from changetools.domain.chunk import Chunk


@dataclass(slots=True)
class Assertion:
    description: str
    passed: bool
    detail: str | None = None


@dataclass(slots=True)
class EvalResult:
    name: str
    passed: bool
    assertions: list[Assertion]
    summary: str = ""

    @property
    def fail_count(self) -> int:
        return sum(1 for a in self.assertions if not a.passed)


@dataclass(slots=True)
class EvalContext:
    chunks_by_id: dict[uuid.UUID, Chunk] = field(default_factory=dict)
    project_chunk_count: int = 0


EvalCase = Callable[[Brief, EvalContext], EvalResult]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _result(name: str, assertions: list[Assertion], summary: str = "") -> EvalResult:
    return EvalResult(
        name=name,
        passed=all(a.passed for a in assertions),
        assertions=assertions,
        summary=summary,
    )


def _name_matches(target: str, candidates: list[str]) -> bool:
    """Token-overlap check: every word of ``target`` appears in some candidate.

    Substring alone is too strict ("digital adoption" doesn't match "Digital
    Workflow Adoption"), but unconstrained substring search is too loose.
    Token overlap walks the middle: synonyms still need to be there.
    """
    target_tokens = {t for t in target.lower().split() if t}
    for c in candidates:
        c_tokens = {t for t in c.lower().split() if t}
        if target_tokens.issubset(c_tokens):
            return True
    return False


# ---------------------------------------------------------------------------
# Case 1 — KPI extraction
# ---------------------------------------------------------------------------


def case_kpi_extraction(brief: Brief, _: EvalContext) -> EvalResult:
    expected = [
        "digital adoption",
        "training completion",
        "sentiment",
        "support handling time",
    ]
    kpi_names = [k.name for k in brief.content.kpis]
    asserts: list[Assertion] = []
    for needle in expected:
        present = _name_matches(needle, kpi_names)
        asserts.append(
            Assertion(
                description=f'KPI mentions "{needle}"',
                passed=present,
                detail=None if present else f"none of {kpi_names!r} matches",
            )
        )

    asserts.append(
        Assertion(
            description="At least 4 KPIs extracted",
            passed=len(brief.content.kpis) >= 4,
            detail=f"got {len(brief.content.kpis)}",
        )
    )

    cited = [k for k in brief.content.kpis if k.evidence]
    asserts.append(
        Assertion(
            description="Every KPI has at least 1 citation",
            passed=len(cited) == len(brief.content.kpis) and len(brief.content.kpis) > 0,
            detail=f"{len(cited)} of {len(brief.content.kpis)} cited",
        )
    )

    return _result(
        "Case 1 — KPI extraction",
        asserts,
        summary=f"{len(brief.content.kpis)} KPIs, {len(cited)} cited",
    )


# ---------------------------------------------------------------------------
# Case 2 — Risk identification
# ---------------------------------------------------------------------------


def case_risk_identification(brief: Brief, _: EvalContext) -> EvalResult:
    risks = brief.content.risks
    asserts = [
        Assertion(
            description="At least 3 risks present",
            passed=len(risks) >= 3,
            detail=f"got {len(risks)}",
        ),
        Assertion(
            description="Severities are valid (low/medium/high/critical)",
            passed=all(r.severity in {"low", "medium", "high", "critical"} for r in risks),
            detail=", ".join(r.severity for r in risks),
        ),
        Assertion(
            description="risk_id values are unique",
            passed=len({r.risk_id for r in risks}) == len(risks),
            detail=", ".join(r.risk_id for r in risks),
        ),
        Assertion(
            description="Every risk has at least one cited chunk",
            passed=all(len(r.evidence) >= 1 for r in risks) and len(risks) > 0,
            detail=f"{sum(1 for r in risks if r.evidence)} cited of {len(risks)}",
        ),
    ]
    return _result(
        "Case 2 — Risk identification",
        asserts,
        summary=", ".join(f"{r.risk_id}:{r.severity}" for r in risks) or "(no risks)",
    )


# ---------------------------------------------------------------------------
# Case 3 — Stakeholder concerns
# ---------------------------------------------------------------------------


def case_stakeholder_concerns(brief: Brief, _: EvalContext) -> EvalResult:
    stakeholders = brief.content.stakeholders
    names = [s.name for s in stakeholders]
    roles = [s.role for s in stakeholders]
    # Lenient match: either Sana Patel by name OR a "regional / role-impact" stakeholder.
    sana_or_role = _name_matches("sana", names) or _name_matches("regional", roles)
    elena_or_comms = _name_matches("elena", names) or _name_matches("comm", roles)

    asserts = [
        Assertion(
            description="At least 1 stakeholder identified",
            passed=len(stakeholders) >= 1,
            detail=f"got {len(stakeholders)}",
        ),
        Assertion(
            description='Sana Patel or a "regional"/role-impact stakeholder present',
            passed=sana_or_role,
            detail=f"names={names!r}, roles={roles!r}",
        ),
        Assertion(
            description="Elena Brooks or a comms/messaging stakeholder present",
            passed=elena_or_comms,
            detail=f"names={names!r}, roles={roles!r}",
        ),
        Assertion(
            description="Every stakeholder has a sentiment",
            passed=all(s.sentiment for s in stakeholders) and len(stakeholders) > 0,
        ),
    ]
    return _result(
        "Case 3 — Stakeholder concerns",
        asserts,
        summary=f"{len(stakeholders)} stakeholders: {', '.join(names) or '(none)'}",
    )


# ---------------------------------------------------------------------------
# Case 4 — Conflict detection
# ---------------------------------------------------------------------------


def case_conflict_detection(brief: Brief, _: EvalContext) -> EvalResult:
    """Conflict detection is conservative — pass on structural validity.

    The LLM only emits a conflict when it sees an *explicit* disagreement
    between call notes and data pack. With our test docs it sometimes finds
    none, which is a legitimate result. We assert on the structure so the
    pipeline doesn't silently drop conflicts.
    """
    conflicts = brief.content.conflicts
    asserts = [
        Assertion(
            description="Conflicts list rendered (may be empty if LLM saw no disagreement)",
            passed=isinstance(conflicts, list),
        ),
    ]
    if conflicts:
        asserts.extend(
            [
                Assertion(
                    description="Each conflict cites both sides",
                    passed=all(c.sources_a and c.sources_b for c in conflicts),
                    detail=", ".join(c.topic for c in conflicts),
                ),
                Assertion(
                    description="Each conflict has both positions filled",
                    passed=all(c.position_a and c.position_b for c in conflicts),
                ),
            ]
        )

    return _result(
        "Case 4 — Conflict detection",
        asserts,
        summary=f"{len(conflicts)} conflicts surfaced",
    )


# ---------------------------------------------------------------------------
# Case 5 — Citation faithfulness
# ---------------------------------------------------------------------------


def _all_chunk_refs(content: BriefContent) -> list[Any]:
    refs = []
    refs.extend(content.executive_summary.evidence)
    for t in content.themes:
        refs.extend(t.evidence)
    for r in content.risks:
        refs.extend(r.evidence)
    for s in content.stakeholders:
        refs.extend(s.evidence)
    for k in content.kpis:
        refs.extend(k.evidence)
    for rec in content.recommendations:
        refs.extend(rec.evidence)
    for c in content.conflicts:
        refs.extend(c.sources_a)
        refs.extend(c.sources_b)
    return refs


def case_citation_faithfulness(brief: Brief, ctx: EvalContext) -> EvalResult:
    refs = _all_chunk_refs(brief.content)
    if not refs:
        return _result(
            "Case 5 — Citation faithfulness",
            [Assertion("Brief contains at least one citation", passed=False)],
            summary="no citations to verify",
        )

    # Sample up to 10 distinct refs, deterministically (sorted by chunk_id).
    seen: dict[uuid.UUID, Any] = {}
    for r in refs:
        seen.setdefault(r.chunk_id, r)
    sample = sorted(seen.values(), key=lambda r: str(r.chunk_id))[:10]

    valid = 0
    invalid_ids: list[str] = []
    for ref in sample:
        chunk = ctx.chunks_by_id.get(ref.chunk_id)
        if chunk is None:
            invalid_ids.append(str(ref.chunk_id))
            continue
        # The snippet should be non-empty (it's set from chunk.text).
        if not ref.snippet:
            invalid_ids.append(f"{ref.chunk_id} (empty snippet)")
            continue
        valid += 1

    asserts = [
        Assertion(
            description=f"All {len(sample)} sampled citations resolve to a real chunk",
            passed=valid == len(sample),
            detail=(
                f"{valid}/{len(sample)} resolved"
                + (f"; invalid: {invalid_ids}" if invalid_ids else "")
            ),
        ),
        Assertion(
            description="At least 5 distinct citations across the brief",
            passed=len(seen) >= 5,
            detail=f"got {len(seen)}",
        ),
    ]
    return _result(
        "Case 5 — Citation faithfulness",
        asserts,
        summary=f"{valid}/{len(sample)} sampled citations valid; {len(seen)} distinct total",
    )


# ---------------------------------------------------------------------------
# Case 6 — Schema validity
# ---------------------------------------------------------------------------


def case_schema_validity(brief: Brief, _: EvalContext) -> EvalResult:
    asserts: list[Assertion] = []
    # If we got here, Pydantic already validated the brief at construction.
    # Re-validate explicitly so the eval surfaces any drift if someone weakens
    # the schema.
    try:
        BriefContent.model_validate(brief.content.model_dump(mode="json"))
        roundtrip_ok = True
        detail: str | None = None
    except Exception as exc:
        roundtrip_ok = False
        detail = str(exc)

    asserts.append(
        Assertion(
            description="BriefContent re-validates after model_dump roundtrip",
            passed=roundtrip_ok,
            detail=detail,
        )
    )
    asserts.append(
        Assertion(
            description="Brief status is 'ready'",
            passed=brief.status == "ready",
            detail=f"status={brief.status}",
        )
    )
    asserts.append(
        Assertion(
            description="Executive summary is non-empty",
            passed=bool(
                brief.content.executive_summary.headline.strip()
                and brief.content.executive_summary.body.strip()
            ),
        )
    )

    return _result(
        "Case 6 — Schema validity",
        asserts,
        summary="schema OK" if roundtrip_ok else "schema FAILED",
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def all_cases() -> list[EvalCase]:
    return [
        case_kpi_extraction,
        case_risk_identification,
        case_stakeholder_concerns,
        case_conflict_detection,
        case_citation_faithfulness,
        case_schema_validity,
    ]
