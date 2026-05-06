"""Markdown report writer for eval runs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path

from changetools.config import Settings
from changetools.domain.brief import Brief
from changetools.eval.cases import EvalResult


def render_markdown(
    *,
    brief: Brief,
    project_id: uuid.UUID,
    project_name: str,
    results: list[EvalResult],
    settings: Settings,
    elapsed_seconds: float,
) -> str:
    overall_pass = all(r.passed for r in results)
    fail_count = sum(r.fail_count for r in results)

    lines: list[str] = []
    lines.append("# ChangeTools — eval report")
    lines.append("")
    lines.append(
        f"_Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} in {elapsed_seconds:.1f}s_"
    )
    lines.append("")
    status_badge = "✅ PASS" if overall_pass else f"❌ FAIL ({fail_count} assertions)"
    lines.append(f"## Status: {status_badge}")
    lines.append("")
    lines.append("## Run context")
    lines.append("")
    lines.append(f"- **Project**: `{project_name}` (`{project_id}`)")
    lines.append(f"- **Brief**: `{brief.id}` (v{brief.version}, status `{brief.status}`)")
    lines.append(f"- **Provider/model**: `{brief.provider}/{brief.model_name}`")
    lines.append(f"- **Embedding provider**: `{settings.embedding_provider}`")
    tracing = "enabled" if settings.langchain_tracing_v2 else "disabled"
    lines.append(f"- **LangSmith tracing**: {tracing}")
    if settings.langchain_tracing_v2:
        lines.append(f"  - Project: `{settings.langchain_project}`")
        lines.append(
            f"  - Dashboard: <https://smith.langchain.com/o/-/projects/p/"
            f"{settings.langchain_project}>"
        )
    if brief.metrics:
        lines.append("- **Metrics**:")
        for k, v in brief.metrics.items():
            lines.append(f"  - `{k}`: {v}")
    lines.append("")

    lines.append("## Cases")
    lines.append("")
    lines.append("| # | Case | Result | Summary |")
    lines.append("|---|------|--------|---------|")
    for i, r in enumerate(results, start=1):
        emoji = "✅" if r.passed else "❌"
        lines.append(f"| {i} | {r.name} | {emoji} | {r.summary or '—'} |")
    lines.append("")

    for r in results:
        lines.append(f"### {r.name}")
        lines.append("")
        lines.append(f"- **Result**: {'✅ PASS' if r.passed else '❌ FAIL'}")
        if r.summary:
            lines.append(f"- **Summary**: {r.summary}")
        lines.append("- **Assertions**:")
        for a in r.assertions:
            check = "✅" if a.passed else "❌"
            line = f"  - {check} {a.description}"
            if a.detail:
                line += f" — _{a.detail}_"
            lines.append(line)
        lines.append("")

    return "\n".join(lines) + "\n"


def write_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
