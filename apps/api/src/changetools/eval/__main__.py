"""CLI entrypoint: ``python -m changetools.eval``.

Examples:
  # Default: pick the most recent project's most recent brief, write the
  # report to ``../../eval_report.md`` (repo root).
  python -m changetools.eval

  # Pin a specific project + brief.
  python -m changetools.eval --project-id <uuid> --brief-id <uuid>

  # Custom output path.
  python -m changetools.eval --output /tmp/report.md
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.db import get_engine
from changetools.eval.runner import run_eval
from changetools.repositories.models import ProjectORM

# apps/api/src/changetools/eval/__main__.py → repo root is six levels up.
DEFAULT_REPORT_PATH = Path(__file__).resolve().parents[4].parent / "eval_report.md"


async def _default_project_id() -> uuid.UUID | None:
    sm = async_sessionmaker(get_engine(), expire_on_commit=False)
    async with sm() as session:
        result = await session.execute(
            select(ProjectORM).order_by(desc(ProjectORM.updated_at)).limit(1)
        )
        row = result.scalar_one_or_none()
        return row.id if row else None


async def _amain(args: argparse.Namespace) -> int:
    project_id = uuid.UUID(args.project_id) if args.project_id else await _default_project_id()
    if project_id is None:
        print("No projects found in database. Create a project first.", file=sys.stderr)
        return 2

    brief_id = uuid.UUID(args.brief_id) if args.brief_id else None
    output = Path(args.output).resolve() if args.output else DEFAULT_REPORT_PATH

    overall_pass, results, brief = await run_eval(
        project_id=project_id, brief_id=brief_id, output_path=output
    )

    fails = sum(r.fail_count for r in results)
    status = "PASS" if overall_pass else f"FAIL ({fails} assertions)"
    print(f"Eval {status} — brief {brief.id} v{brief.version}")
    print(f"Report: {output}")
    for r in results:
        flag = "✓" if r.passed else "✗"
        print(f"  {flag} {r.name} — {r.summary}")

    return 0 if overall_pass else 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="changetools.eval")
    parser.add_argument(
        "--project-id",
        help="Project UUID. Defaults to the most recently updated project.",
    )
    parser.add_argument(
        "--brief-id",
        help="Brief UUID. Defaults to the latest brief in the project.",
    )
    parser.add_argument(
        "--output",
        help=f"Report output path (default: {DEFAULT_REPORT_PATH}).",
    )
    args = parser.parse_args()
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    sys.exit(main())
