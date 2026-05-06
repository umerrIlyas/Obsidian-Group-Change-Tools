"""LLM draft of every section.

Each section gets its own prompt + structured-output schema, so a single
section failing validation only forces a re-draft of that section in the
``validate`` node — not the whole brief.

Concurrency is bounded by ``MAX_CONCURRENT_DRAFTS`` (default 2). Groq's
free tier has aggressive RPM limits and fanning out all 6 sections at
once hits 429s; 2-at-a-time gets us most of the latency win without
tripping the limiter.
"""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.language_models import BaseChatModel

from changetools.agents.generation.evidence import format_chunks_for_prompt
from changetools.agents.generation.schemas import SECTION_SCHEMAS
from changetools.agents.generation.state import SECTION_NAMES, GenerationState
from changetools.agents.prompts.sections import (
    CHUNKS_HEADER,
    SECTION_PROMPTS,
    SYSTEM,
)
from changetools.core.errors import ProviderError
from changetools.infrastructure.llm.base import LLMProvider

MAX_CONCURRENT_DRAFTS = 2


async def _draft_one(
    section: str,
    state: GenerationState,
    chat_model: BaseChatModel,
    semaphore: asyncio.Semaphore,
) -> tuple[str, Any | str]:
    """Call the LLM for a single section. Returns ``(section, parsed_or_error)``."""
    schema = SECTION_SCHEMAS[section]
    instruction = SECTION_PROMPTS[section]
    hits = state.evidence.get(section, [])
    chunks_block = format_chunks_for_prompt(hits) or "(no chunks retrieved)"

    user_prompt = (
        f"{instruction}\n\n{CHUNKS_HEADER}{chunks_block}\n\n"
        "Return JSON only — no prose, no markdown."
    )

    structured = chat_model.with_structured_output(schema)
    async with semaphore:
        try:
            result = await structured.ainvoke(
                [
                    ("system", SYSTEM),
                    ("user", user_prompt),
                ]
            )
        except Exception as exc:
            return section, f"LLM call failed: {exc.__class__.__name__}: {exc}"
    return section, result


def make_draft_sections_node(llm: LLMProvider):
    async def draft_sections_node(state: GenerationState) -> dict:
        # Skip sections that are already drafted AND not in the failure set —
        # this lets the validation retry loop only re-draft what failed.
        failed = set(state.validation_errors.keys())
        sections_to_draft = [
            s for s in SECTION_NAMES if s not in state.drafts or s in failed
        ]

        chat_model = llm.chat_model(temperature=0.2, max_tokens=2400)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DRAFTS)

        results = await asyncio.gather(
            *(_draft_one(s, state, chat_model, semaphore) for s in sections_to_draft)
        )

        new_drafts = {**state.drafts}
        new_errors = dict(state.validation_errors)
        had_call_failure = False
        for section, parsed in results:
            if isinstance(parsed, str):
                # LLM call itself failed (network / rate limit / parse).
                new_errors[section] = parsed
                had_call_failure = True
                continue
            new_drafts[section] = parsed.model_dump(mode="json")
            new_errors.pop(section, None)

        if had_call_failure and not new_drafts:
            # Total failure on first attempt — abort early so we don't loop.
            raise ProviderError(
                "All draft sections failed; aborting generation",
                code="draft_total_failure",
            )

        return {
            "drafts": new_drafts,
            "validation_errors": new_errors,
            "model_name": llm.model,
            "provider": llm.name,
        }

    return draft_sections_node


draft_sections_node = make_draft_sections_node
