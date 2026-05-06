"""Tests for the structured-output helper with JSON-mode fallback."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage
from pydantic import BaseModel

from changetools.core.errors import ProviderError
from changetools.infrastructure.llm.structured import (
    _extract_text,
    invoke_structured,
)


class _Item(BaseModel):
    title: str
    score: int


def _make_chat_model(
    *,
    structured_raises: Exception | None = None,
    structured_return: Any | None = None,
    json_mode_content: str | Exception | None = None,
) -> MagicMock:
    """Build a mock chat model that fakes ``with_structured_output`` and ``bind``."""
    chat = MagicMock()

    # Path 1: with_structured_output().ainvoke()
    structured_runnable = MagicMock()
    structured_runnable.ainvoke = AsyncMock(
        side_effect=structured_raises if structured_raises else None,
        return_value=structured_return,
    )
    chat.with_structured_output = MagicMock(return_value=structured_runnable)

    # Path 2: bind(response_format=...).ainvoke()
    bound_runnable = MagicMock()
    if isinstance(json_mode_content, Exception):
        bound_runnable.ainvoke = AsyncMock(side_effect=json_mode_content)
    elif json_mode_content is not None:
        bound_runnable.ainvoke = AsyncMock(
            return_value=AIMessage(content=json_mode_content)
        )
    else:
        bound_runnable.ainvoke = AsyncMock(
            return_value=AIMessage(content="(unused)")
        )
    chat.bind = MagicMock(return_value=bound_runnable)

    return chat


@pytest.mark.asyncio
async def test_native_path_returns_structured_output_when_available():
    expected = _Item(title="ok", score=42)
    chat = _make_chat_model(structured_return=expected)

    result = await invoke_structured(chat, schema=_Item, system="s", user="u")

    assert result == expected
    chat.with_structured_output.assert_called_once_with(_Item)
    # Fallback should not have been used.
    chat.bind.assert_not_called()


@pytest.mark.asyncio
async def test_falls_back_to_json_mode_when_structured_output_raises():
    chat = _make_chat_model(
        structured_raises=ValueError("schema rejected (HTTP 400)"),
        json_mode_content='{"title": "fallback", "score": 7}',
    )

    result = await invoke_structured(chat, schema=_Item, system="s", user="u")

    assert isinstance(result, _Item)
    assert result.title == "fallback"
    assert result.score == 7
    chat.bind.assert_called_once()
    # The user prompt on the fallback path should include the JSON schema.
    bound_runnable = chat.bind.return_value
    bound_runnable.ainvoke.assert_called_once()
    args, _ = bound_runnable.ainvoke.call_args
    rendered = " ".join(m[1] for m in args[0])
    assert "SCHEMA" in rendered
    assert "title" in rendered  # schema mentions the field


@pytest.mark.asyncio
async def test_propagates_provider_error_when_both_paths_fail():
    chat = _make_chat_model(
        structured_raises=ValueError("400 from structured path"),
        json_mode_content=ConnectionError("network down"),
    )

    with pytest.raises(ProviderError) as ei:
        await invoke_structured(chat, schema=_Item, system="s", user="u")

    assert ei.value.code == "structured_output_failed"


@pytest.mark.asyncio
async def test_propagates_provider_error_when_fallback_returns_invalid_json():
    chat = _make_chat_model(
        structured_raises=ValueError("400"),
        json_mode_content="this is not json at all",
    )

    with pytest.raises(ProviderError) as ei:
        await invoke_structured(chat, schema=_Item, system="s", user="u")

    assert ei.value.code == "structured_output_invalid"


def test_extract_text_handles_string_content():
    assert _extract_text(AIMessage(content="hello")) == "hello"


def test_extract_text_handles_anthropic_block_list():
    msg = AIMessage(content=[{"type": "text", "text": "from block"}])
    assert _extract_text(msg) == "from block"
