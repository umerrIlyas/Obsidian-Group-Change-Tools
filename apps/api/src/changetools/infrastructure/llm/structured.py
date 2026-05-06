"""Structured-output helper with a JSON-mode fallback.

Some providers (notably Groq with ``llama-3.3-70b-versatile``) reject complex
nested Pydantic schemas when called via ``with_structured_output``. The error
arrives as an HTTP 400 ``Bad Request``, which is *not* recovered by retries —
the schema is the problem.

To stay reliable across providers without abandoning structured output, this
helper:

1. Tries the native structured-output path first (fast, single round-trip).
2. On failure, falls back to JSON mode: re-prompts with the JSON Schema
   appended and parses the response with Pydantic.

The fallback is provider-agnostic — every provider we support (groq, openai,
anthropic, ollama) accepts ``response_format={"type": "json_object"}`` either
natively or through ``BaseChatModel.bind``. If the fallback also fails the
exception propagates so the caller (graph node, tool, etc.) can surface it.

Counter-intuitive note: this is *strictly* better than only using structured
output. When the native path works it costs nothing extra. When it doesn't,
we'd otherwise lose the section entirely. The cost is one extra prompt-token
budget for the schema definition on the fallback round-trip — negligible.
"""

from __future__ import annotations

import json
from typing import TypeVar

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from pydantic import BaseModel, ValidationError

from changetools.core.errors import ProviderError
from changetools.core.logging import get_logger

T = TypeVar("T", bound=BaseModel)

log = get_logger("llm.structured")

# Some provider exceptions don't carry a response object; truncate the
# string form so we don't blow up the log line with a multi-KB body.
_MAX_ERROR_LEN = 400


async def invoke_structured(
    chat_model: BaseChatModel,
    *,
    schema: type[T],
    system: str,
    user: str,
) -> T:
    """Invoke ``chat_model`` and return a validated ``schema`` instance.

    Tries native structured output first; on any failure, retries with a
    JSON-mode prompt that includes the JSON Schema, then validates the
    response. Raises ``ProviderError`` if both paths fail.
    """
    messages: list[BaseMessage | tuple[str, str]] = [
        ("system", system),
        ("user", user),
    ]

    # --- Path 1: native structured output ---
    try:
        structured = chat_model.with_structured_output(schema)
        return await structured.ainvoke(messages)  # type: ignore[return-value]
    except Exception as exc:
        log.warning(
            "structured_output_failed_falling_back",
            schema=schema.__name__,
            error=_short(exc),
        )

    # --- Path 2: JSON mode + manual parse ---
    json_schema_str = json.dumps(schema.model_json_schema(), separators=(",", ":"))
    augmented_user = (
        f"{user}\n\n"
        f"Return JSON matching exactly this schema. Output JSON only — "
        f"no prose, no markdown fences.\n\nSCHEMA: {json_schema_str}"
    )

    try:
        json_model = chat_model.bind(response_format={"type": "json_object"})
    except Exception:
        # Provider doesn't expose a JSON-mode bind — fall through with the
        # plain model, relying on the schema-in-prompt instruction. Less
        # reliable but still works for most modern providers.
        json_model = chat_model

    try:
        response = await json_model.ainvoke(
            [("system", system), ("user", augmented_user)]
        )
    except Exception as exc:
        log.error(
            "json_mode_fallback_failed",
            schema=schema.__name__,
            error=_short(exc),
        )
        raise ProviderError(
            f"LLM call failed (both structured and JSON-mode paths): "
            f"{exc.__class__.__name__}: {_short(exc)}",
            code="structured_output_failed",
        ) from exc

    content = _extract_text(response)
    try:
        return schema.model_validate_json(content)
    except ValidationError as exc:
        log.error(
            "json_mode_fallback_invalid_schema",
            schema=schema.__name__,
            content_preview=content[:200],
        )
        raise ProviderError(
            f"JSON-mode response did not match {schema.__name__}: {exc}",
            code="structured_output_invalid",
        ) from exc


def _extract_text(response: AIMessage | object) -> str:
    """Normalize an LLM response into a single string of JSON content."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        # Some providers (Anthropic) return content as a list of blocks.
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if isinstance(text, str):
                    parts.append(text)
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts).strip()
    return str(content).strip()


def _short(exc: BaseException) -> str:
    s = f"{exc.__class__.__name__}: {exc}"
    return s if len(s) <= _MAX_ERROR_LEN else s[: _MAX_ERROR_LEN - 1] + "…"
