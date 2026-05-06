"""Validate the LLM drafts against their Pydantic schemas.

Validation is double-checked here even though ``with_structured_output``
already validates: provider/parse hiccups can still leak through, and the
retry loop benefits from a single chokepoint.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import ValidationError

from changetools.agents.generation.schemas import SECTION_SCHEMAS
from changetools.agents.generation.state import SECTION_NAMES, GenerationState


async def validate_node(state: GenerationState) -> dict:
    errors: dict[str, str] = {}
    for section in SECTION_NAMES:
        draft = state.drafts.get(section)
        if draft is None:
            errors[section] = "missing draft"
            continue
        schema = SECTION_SCHEMAS[section]
        try:
            schema.model_validate(draft)
        except ValidationError as exc:
            errors[section] = _short_validation_error(exc)
    return {
        "validation_errors": errors,
        "retry_count": state.retry_count + (1 if errors else 0),
    }


def should_retry_after_validation(state: GenerationState) -> Literal["draft", "cite"]:
    """Conditional edge function — route either back to draft or onward."""
    if not state.validation_errors:
        return "cite"
    if state.retry_count > state.max_retries:
        return "cite"  # give up retrying; cite_evidence handles partial drafts
    return "draft"


def _short_validation_error(exc: ValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors()[:3]:
        loc = ".".join(str(x) for x in err["loc"])
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


# unused import guard for type-only references
_: Any = SECTION_NAMES
