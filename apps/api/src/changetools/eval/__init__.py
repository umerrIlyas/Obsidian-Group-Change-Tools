"""Evaluation harness for the brief-generation pipeline.

Scope:
  * Run a fixed suite of 6 cases against a generated Brief
  * Emit a markdown report (eval_report.md) and exit non-zero if any case fails
  * Surface LangSmith trace status so the report points at the dashboard

Invocation: ``python -m changetools.eval --project-id <uuid>``.

Cases stay deterministic given a brief — they don't call the LLM themselves;
they assert on what the generation pipeline produced. That keeps the eval
fast, cheap, and resilient to the upstream Groq free-tier rate limit.
"""

from changetools.eval.cases import EvalCase, EvalResult, all_cases
from changetools.eval.report import write_report

__all__ = ["EvalCase", "EvalResult", "all_cases", "write_report"]
