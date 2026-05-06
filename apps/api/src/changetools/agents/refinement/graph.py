"""Compile the refinement ReAct agent.

We use ``langgraph.prebuilt.create_react_agent`` rather than rolling our own
loop: it gives tool calling, retry semantics, and message-history threading
for free, all with the same SSE-friendly streaming API as the generation
graph.
"""

from __future__ import annotations

from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from changetools.infrastructure.llm.base import LLMProvider

SYSTEM_PROMPT = """You are the ChangeTools refinement assistant.

Your job is to help a senior change-management consultant tweak a Change
Strategy Brief and its slide deck. You have read/write access to the brief
through tools.

Rules:
1. Always read the relevant section before updating it (read_brief_section).
2. Before drafting *new* content, call retrieve_evidence to ground claims in
   actual source chunks. Carry the chunk_id and document_id values verbatim
   into the evidence field of any new items.
3. update_brief_section creates a new brief VERSION — the previous version is
   preserved. After updating, call regenerate_deck so the slide deck matches.
4. When the user asks for a small change (e.g. tighten the exec summary,
   raise risk severity), keep the rest of the section unchanged.
5. Be terse. Confirm what you did in 1-2 sentences. Don't paste the full
   updated section back unless asked — link by section name.
6. If a request is ambiguous or destructive, ask one clarifying question
   instead of guessing.
"""


def build_refinement_agent(
    *,
    llm: LLMProvider,
    tools: list[BaseTool],
):
    """Return a compiled LangGraph ReAct agent.

    ``tools`` should be the per-project tool set returned by
    ``agents.refinement.tools.build_tools()``.
    """
    chat_model = llm.chat_model(temperature=0.2, max_tokens=2400)
    return create_react_agent(
        model=chat_model,
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )
