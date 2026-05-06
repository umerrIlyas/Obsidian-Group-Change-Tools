"""ChatService — runs the refinement agent and persists the conversation.

The service yields ``StreamEvent``s as the agent works so the API layer can
forward them as SSE. Persistence is split into two writes per turn:

  * a "user" message at the start (so the message appears in history even if
    the LLM call fails)
  * a single "assistant" message at the end with the final content + a list
    of all ``ToolCall``s that fired during the turn

Tool input/output messages are *also* persisted so the UI can render the
intermediate steps when reloading a session.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.agents.refinement.graph import build_refinement_agent
from changetools.agents.refinement.tools import build_tools
from changetools.core.errors import NotFoundError
from changetools.core.logging import get_logger
from changetools.domain.chat import ChatMessage, ChatSession, ToolCall
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.infrastructure.llm.base import LLMProvider
from changetools.repositories.chat import ChatRepository
from changetools.repositories.projects import ProjectRepository
from changetools.services.deck_service import DeckService

log = get_logger("chat_service")


@dataclass(slots=True)
class StreamEvent:
    """Event emitted while the agent runs."""

    kind: str  # "token" | "tool_start" | "tool_end" | "brief_updated" | "final" | "error"
    detail: dict[str, Any]


class ChatService:
    def __init__(
        self,
        *,
        sessionmaker: async_sessionmaker,  # type: ignore[type-arg]
        llm: LLMProvider,
        embeddings: EmbeddingProvider,
        deck_service: DeckService,
    ) -> None:
        self._sm = sessionmaker
        self._llm = llm
        self._embeddings = embeddings
        self._deck = deck_service

    # --- session/message reads ---

    async def list_sessions(self, project_id: uuid.UUID) -> list[ChatSession]:
        async with self._sm() as session:
            return await ChatRepository(session).list_sessions_by_project(project_id)

    async def list_messages(self, session_id: uuid.UUID) -> list[ChatMessage]:
        async with self._sm() as session:
            return await ChatRepository(session).list_messages(session_id)

    async def get_or_create_session(
        self, project_id: uuid.UUID, *, session_id: uuid.UUID | None
    ) -> ChatSession:
        async with self._sm() as session:
            project = await ProjectRepository(session).get(project_id)
            if project is None:
                raise NotFoundError(f"Project not found: {project_id}")
            if session_id is not None:
                existing = await ChatRepository(session).get_session(session_id)
                if existing is None:
                    raise NotFoundError(f"Chat session not found: {session_id}")
                if existing.project_id != project_id:
                    raise NotFoundError("Session does not belong to this project")
                return existing
            new = await ChatRepository(session).create_session(project_id=project_id)
            await session.commit()
            return new

    # --- agent run ---

    async def stream_response(
        self,
        *,
        project_id: uuid.UUID,
        session_id: uuid.UUID,
        user_message: str,
    ) -> AsyncIterator[StreamEvent]:
        """Run the agent and yield streaming events. Persists messages as it goes."""
        # 1. Persist user message immediately so the UI sees it on reload.
        async with self._sm() as session:
            await ChatRepository(session).add_message(
                session_id=session_id, role="user", content=user_message
            )
            await session.commit()

        # 2. Pull message history for the agent's input.
        history = await self.list_messages(session_id)
        lc_history = _to_langchain_messages(history)

        # 3. Track brief-update side effects so we can emit progress events.
        brief_updates: list[dict[str, Any]] = []

        def _on_brief_updated(detail: dict[str, Any]) -> None:
            brief_updates.append(detail)

        tools = build_tools(
            project_id=project_id,
            sessionmaker=self._sm,
            embeddings=self._embeddings,
            deck_service=self._deck,
            on_brief_updated=_on_brief_updated,
        )
        agent = build_refinement_agent(llm=self._llm, tools=tools)

        # 4. Stream events.
        seen_tool_calls: dict[str, ToolCall] = {}
        seen_tool_results: list[dict[str, Any]] = []
        final_text = ""
        consumed_brief_updates = 0

        try:
            async for event in agent.astream_events(
                {"messages": lc_history}, version="v2"
            ):
                etype = event["event"]
                data = event.get("data", {})

                if etype == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    text = getattr(chunk, "content", None) if chunk else None
                    if text:
                        final_text += text
                        yield StreamEvent("token", {"text": text})

                elif etype == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = data.get("input") or {}
                    tc_id = event.get("run_id", uuid.uuid4().hex)
                    seen_tool_calls[tc_id] = ToolCall(
                        id=tc_id, name=tool_name, args=_safe_args(tool_input)
                    )
                    yield StreamEvent(
                        "tool_start",
                        {
                            "id": tc_id,
                            "name": tool_name,
                            "args": _safe_args(tool_input),
                        },
                    )

                elif etype == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    tc_id = event.get("run_id", "")
                    output = data.get("output")
                    output_text = _stringify(output)
                    seen_tool_results.append(
                        {"id": tc_id, "name": tool_name, "output": output_text}
                    )
                    yield StreamEvent(
                        "tool_end",
                        {"id": tc_id, "name": tool_name, "output": output_text},
                    )

                # Drain any brief-updated callbacks that fired since the last loop.
                while consumed_brief_updates < len(brief_updates):
                    yield StreamEvent(
                        "brief_updated", brief_updates[consumed_brief_updates]
                    )
                    consumed_brief_updates += 1
        except Exception as exc:
            log.exception("chat.stream_failed", session_id=str(session_id))
            await self._persist_assistant(
                session_id, content=f"(error) {exc}", tool_calls=[]
            )
            yield StreamEvent("error", {"message": str(exc)})
            return

        # 5. Drain any straggling brief updates emitted after the last yield.
        while consumed_brief_updates < len(brief_updates):
            yield StreamEvent("brief_updated", brief_updates[consumed_brief_updates])
            consumed_brief_updates += 1

        # 6. Persist assistant + tool messages.
        await self._persist_tool_messages(session_id, seen_tool_calls, seen_tool_results)
        await self._persist_assistant(
            session_id,
            content=final_text,
            tool_calls=list(seen_tool_calls.values()),
        )
        await self._touch_session(session_id)

        yield StreamEvent(
            "final",
            {
                "content": final_text,
                "tool_calls": [tc.model_dump() for tc in seen_tool_calls.values()],
                "brief_updates": brief_updates,
            },
        )

    # --- persistence helpers ---

    async def _persist_assistant(
        self,
        session_id: uuid.UUID,
        *,
        content: str,
        tool_calls: list[ToolCall],
    ) -> None:
        async with self._sm() as session:
            await ChatRepository(session).add_message(
                session_id=session_id,
                role="assistant",
                content=content,
                tool_calls=tool_calls,
            )
            await session.commit()

    async def _persist_tool_messages(
        self,
        session_id: uuid.UUID,
        calls: dict[str, ToolCall],
        results: list[dict[str, Any]],
    ) -> None:
        if not results:
            return
        async with self._sm() as session:
            for r in results:
                tc = calls.get(r["id"])
                await ChatRepository(session).add_message(
                    session_id=session_id,
                    role="tool",
                    content=r["output"][:8000],
                    tool_call_id=r["id"],
                    tool_name=r["name"],
                    meta={"args": tc.args if tc else {}},
                )
            await session.commit()

    async def _touch_session(self, session_id: uuid.UUID) -> None:
        async with self._sm() as session:
            await ChatRepository(session).touch_session(session_id)
            await session.commit()


# ---------------------------------------------------------------------------
# Conversion helpers
# ---------------------------------------------------------------------------


def _to_langchain_messages(history: list[ChatMessage]):
    """Replay persisted messages into the LangChain message history format.

    For simplicity we replay user + assistant turns only — the agent will
    re-derive tool calls from the conversation. Including tool messages
    verbatim would require matching their tool_call_ids back to the assistant
    AIMessage that referenced them, which langgraph rebuilds itself.
    """
    out = []
    for m in history:
        if m.role == "user":
            out.append(HumanMessage(content=m.content))
        elif m.role == "assistant" and m.content:
            out.append(AIMessage(content=m.content))
        # tool / system roles are dropped during replay
    return out


def _safe_args(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {k: _stringify(v)[:1000] for k, v in value.items()}
    return {"input": _stringify(value)[:1000]}


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, ToolMessage):
        return str(value.content)
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


# Used to keep asyncio import live for editors that drop unused names.
_ = asyncio
