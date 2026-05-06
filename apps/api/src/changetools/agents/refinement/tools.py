"""Tools the refinement agent can call.

Each tool is a closure over the per-request services and the project_id, so
the agent doesn't need to thread context through every call. Returns are
plain strings (JSON when structured) — LangGraph turns them into
``ToolMessage``s automatically.

Tool surface:
  retrieve_evidence(query, top_k)
  read_brief_section(section)
  update_brief_section(section, new_value_json)
  regenerate_deck()
  list_risks() / list_kpis() / list_stakeholders()
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.core.errors import NotFoundError
from changetools.domain.brief import (
    KPI,
    Brief,
    BriefContent,
    Conflict,
    ExecutiveSummary,
    Recommendation,
    Risk,
    Stakeholder,
    Theme,
)
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.repositories.briefs import BriefRepository
from changetools.services.deck_service import DeckService
from changetools.services.retrieval_service import RetrievalService

VALID_SECTIONS = {
    "executive_summary",
    "themes",
    "risks",
    "stakeholders",
    "kpis",
    "recommendations",
    "conflicts",
}

SECTION_MODELS: dict[str, type[BaseModel]] = {
    "executive_summary": ExecutiveSummary,
    "themes": Theme,
    "risks": Risk,
    "stakeholders": Stakeholder,
    "kpis": KPI,
    "recommendations": Recommendation,
    "conflicts": Conflict,
}


# ---------------------------------------------------------------------------
# Tool argument schemas (used to surface clean OpenAPI to the model)
# ---------------------------------------------------------------------------


class RetrieveEvidenceArgs(BaseModel):
    query: str = Field(..., description="Natural-language search query.")
    top_k: int = Field(6, ge=1, le=20, description="Max chunks to return.")


class ReadSectionArgs(BaseModel):
    section: str = Field(
        ...,
        description=(
            "One of: executive_summary, themes, risks, stakeholders, "
            "kpis, recommendations, conflicts"
        ),
    )


class UpdateSectionArgs(BaseModel):
    section: str = Field(
        ...,
        description=(
            "One of: executive_summary, themes, risks, stakeholders, "
            "kpis, recommendations, conflicts"
        ),
    )
    new_value_json: str = Field(
        ...,
        description=(
            "Full JSON for the new section value. For executive_summary, an "
            "object with headline, body, evidence, confidence. For list "
            "sections (themes, risks, etc.), a JSON array of items. "
            "Evidence chunks must include chunk_id and document_id UUIDs from "
            "prior retrieve_evidence calls."
        ),
    )


class NoArgs(BaseModel):
    pass


# ---------------------------------------------------------------------------
# Tool factory
# ---------------------------------------------------------------------------


def build_tools(
    *,
    project_id: uuid.UUID,
    sessionmaker: async_sessionmaker,  # type: ignore[type-arg]
    embeddings: EmbeddingProvider,
    deck_service: DeckService,
    on_brief_updated: Any | None = None,
) -> list[StructuredTool]:
    """Return the tool set bound to ``project_id``.

    ``on_brief_updated`` is an optional callback (sync or async-callable) that
    fires whenever ``update_brief_section`` produces a new brief version. The
    SSE handler uses it to emit a 'brief_updated' progress event.
    """

    sm = sessionmaker

    async def _retrieve_evidence(query: str, top_k: int = 6) -> str:
        async with sm() as session:
            service = RetrievalService(session=session, embeddings=embeddings)
            hits = await service.retrieve(
                project_id=project_id, query=query, top_k=top_k
            )
        if not hits:
            return "No matching chunks. Try a different query."
        rendered = []
        for h in hits:
            rendered.append(
                {
                    "chunk_id": str(h.chunk.id),
                    "document_id": str(h.chunk.document_id),
                    "document": h.document_filename,
                    "score": round(h.score, 3),
                    "snippet": (
                        h.chunk.text[:400] + "…"
                        if len(h.chunk.text) > 400
                        else h.chunk.text
                    ),
                }
            )
        return json.dumps(rendered, indent=2)

    async def _latest_brief() -> Brief:
        async with sm() as session:
            brief = await BriefRepository(session).latest_for_project(project_id)
        if brief is None:
            raise NotFoundError("No brief exists yet — generate one first.")
        return brief

    async def _read_brief_section(section: str) -> str:
        if section not in VALID_SECTIONS:
            return f"Invalid section. Use one of: {sorted(VALID_SECTIONS)}"
        brief = await _latest_brief()
        value: Any = getattr(brief.content, section)
        if hasattr(value, "model_dump"):
            value = value.model_dump(mode="json")
        elif isinstance(value, list):
            value = [
                v.model_dump(mode="json") if hasattr(v, "model_dump") else v
                for v in value
            ]
        return json.dumps(value, indent=2)

    async def _update_brief_section(section: str, new_value_json: str) -> str:
        if section not in VALID_SECTIONS:
            return f"Invalid section. Use one of: {sorted(VALID_SECTIONS)}"

        try:
            payload = json.loads(new_value_json)
        except json.JSONDecodeError as exc:
            return f"Invalid JSON: {exc}"

        # Validate the payload against the expected schema for this section.
        model_cls = SECTION_MODELS[section]
        try:
            if section == "executive_summary":
                if not isinstance(payload, dict):
                    return "executive_summary must be a JSON object"
                validated: Any = model_cls.model_validate(payload)
            else:
                if not isinstance(payload, list):
                    return f"{section} must be a JSON array of items"
                validated = [model_cls.model_validate(item) for item in payload]
        except Exception as exc:
            return f"Schema validation failed: {exc}"

        # Read latest, build updated content, write a new brief version.
        async with sm() as session:
            current = await BriefRepository(session).latest_for_project(project_id)
            if current is None:
                return "No brief exists yet — generate one first."

            new_content_dict = current.content.model_dump(mode="json")
            new_content_dict[section] = (
                validated.model_dump(mode="json")
                if hasattr(validated, "model_dump")
                else [v.model_dump(mode="json") for v in validated]
            )
            new_content = BriefContent.model_validate(new_content_dict)

            new_metrics = {
                **current.metrics,
                "derived_from_brief_id": str(current.id),
                "refined_section": section,
            }

            new_brief = await BriefRepository(session).create(
                project_id=project_id,
                status="ready",
                model_name=current.model_name,
                provider=current.provider,
            )
            await BriefRepository(session).update_content(
                new_brief.id,
                status="ready",
                content=new_content,
                metrics=new_metrics,
                error=None,
            )
            await session.commit()

        if on_brief_updated is not None:
            try:
                result = on_brief_updated(
                    {
                        "brief_id": str(new_brief.id),
                        "version": new_brief.version,
                        "section": section,
                    }
                )
                # Allow async callbacks
                if hasattr(result, "__await__"):
                    await result  # type: ignore[func-returns-value]
            except Exception:  # pragma: no cover - non-fatal
                pass

        return json.dumps(
            {
                "ok": True,
                "new_brief_id": str(new_brief.id),
                "new_version": new_brief.version,
                "section": section,
            }
        )

    async def _regenerate_deck() -> str:
        brief = await _latest_brief()
        deck = await deck_service.render_for_brief(brief.id)
        return json.dumps(
            {
                "ok": True,
                "deck_id": str(deck.id),
                "brief_id": str(brief.id),
                "slide_count": deck.slide_count,
                "has_pdf": deck.pdf_storage_key is not None,
            }
        )

    async def _list_named(section: str) -> str:
        brief = await _latest_brief()
        items = getattr(brief.content, section)
        if section == "risks":
            return json.dumps(
                [
                    {
                        "risk_id": r.risk_id,
                        "title": r.title,
                        "severity": r.severity,
                        "owner": r.owner,
                    }
                    for r in items
                ],
                indent=2,
            )
        if section == "kpis":
            return json.dumps(
                [
                    {
                        "name": k.name,
                        "current": k.current_value,
                        "target": k.target_value,
                        "trend": k.trend,
                    }
                    for k in items
                ],
                indent=2,
            )
        if section == "stakeholders":
            return json.dumps(
                [
                    {"name": s.name, "role": s.role, "sentiment": s.sentiment}
                    for s in items
                ],
                indent=2,
            )
        return "[]"

    return [
        StructuredTool.from_function(
            coroutine=_retrieve_evidence,
            name="retrieve_evidence",
            description=(
                "Semantic search over the project's source documents. Returns up "
                "to top_k matching chunks with chunk_id, document_id, and a "
                "snippet. Use chunk_ids when constructing evidence references "
                "for update_brief_section."
            ),
            args_schema=RetrieveEvidenceArgs,
        ),
        StructuredTool.from_function(
            coroutine=_read_brief_section,
            name="read_brief_section",
            description=(
                "Read the current value of one section of the latest brief. "
                "Returns JSON. Always read before update."
            ),
            args_schema=ReadSectionArgs,
        ),
        StructuredTool.from_function(
            coroutine=_update_brief_section,
            name="update_brief_section",
            description=(
                "Replace one section of the brief with new content. Creates a "
                "new brief version (the previous version stays accessible). "
                "Validate with read_brief_section first; preserve evidence "
                "chunk_ids/document_ids from prior retrieve_evidence calls."
            ),
            args_schema=UpdateSectionArgs,
        ),
        StructuredTool.from_function(
            coroutine=_regenerate_deck,
            name="regenerate_deck",
            description=(
                "Re-render the slide deck for the latest brief version. Run "
                "this after update_brief_section so the deck reflects edits."
            ),
            args_schema=NoArgs,
        ),
        StructuredTool.from_function(
            coroutine=lambda: _list_named("risks"),
            name="list_risks",
            description="Return a compact list of risks (id, title, severity, owner).",
            args_schema=NoArgs,
        ),
        StructuredTool.from_function(
            coroutine=lambda: _list_named("kpis"),
            name="list_kpis",
            description="Return a compact list of KPIs (name, current, target, trend).",
            args_schema=NoArgs,
        ),
        StructuredTool.from_function(
            coroutine=lambda: _list_named("stakeholders"),
            name="list_stakeholders",
            description="Return a compact list of stakeholders (name, role, sentiment).",
            args_schema=NoArgs,
        ),
    ]
