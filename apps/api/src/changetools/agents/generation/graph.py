"""Compile the brief-generation graph.

The graph is a fairly linear pipeline with one feedback loop on validation:

    load_context → retrieve_evidence → draft_sections → validate
                                          ▲              │
                                          └──── retry ◀──┘
                                                         │
                            cite_evidence ── detect_conflicts ── assemble ── persist

Each node is a separate function so LangSmith traces show one span per stage.
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph
from sqlalchemy.ext.asyncio import async_sessionmaker

from changetools.agents.generation.nodes import (
    assemble_node,
    cite_evidence_node,
    should_retry_after_validation,
    validate_node,
)
from changetools.agents.generation.nodes.detect_conflicts import (
    make_detect_conflicts_node,
)
from changetools.agents.generation.nodes.draft_sections import make_draft_sections_node
from changetools.agents.generation.nodes.load_context import make_load_context_node
from changetools.agents.generation.nodes.persist import make_persist_node
from changetools.agents.generation.nodes.retrieve_evidence import (
    make_retrieve_evidence_node,
)
from changetools.agents.generation.state import GenerationState
from changetools.infrastructure.embeddings.base import EmbeddingProvider
from changetools.infrastructure.llm.base import LLMProvider


def build_generation_graph(
    *,
    sessionmaker: async_sessionmaker,  # type: ignore[type-arg]
    llm: LLMProvider,
    embeddings: EmbeddingProvider,
):
    """Compile and return the runnable graph."""
    graph = StateGraph(GenerationState)

    graph.add_node("load_context", make_load_context_node(sessionmaker))
    graph.add_node(
        "retrieve_evidence", make_retrieve_evidence_node(sessionmaker, embeddings)
    )
    graph.add_node("draft_sections", make_draft_sections_node(llm))
    graph.add_node("validate", validate_node)
    graph.add_node("cite_evidence", cite_evidence_node)
    graph.add_node("detect_conflicts", make_detect_conflicts_node(llm))
    graph.add_node("assemble", assemble_node)
    graph.add_node("persist", make_persist_node(sessionmaker))

    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "retrieve_evidence")
    graph.add_edge("retrieve_evidence", "draft_sections")
    graph.add_edge("draft_sections", "validate")
    graph.add_conditional_edges(
        "validate",
        should_retry_after_validation,
        {"draft": "draft_sections", "cite": "cite_evidence"},
    )
    graph.add_edge("cite_evidence", "detect_conflicts")
    graph.add_edge("detect_conflicts", "assemble")
    graph.add_edge("assemble", "persist")
    graph.add_edge("persist", END)

    return graph.compile()
