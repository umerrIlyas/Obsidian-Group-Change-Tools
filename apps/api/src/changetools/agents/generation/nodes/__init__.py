"""Graph node implementations.

Each node is a free-standing async function ``async def node(state) -> dict``
returning the partial state patch. LangGraph merges patches into the next
state. Keeping each node a single function (not a class) makes them trivial
to unit-test with hand-built states.
"""

from changetools.agents.generation.nodes.assemble import assemble_node
from changetools.agents.generation.nodes.cite_evidence import cite_evidence_node
from changetools.agents.generation.nodes.detect_conflicts import detect_conflicts_node
from changetools.agents.generation.nodes.draft_sections import draft_sections_node
from changetools.agents.generation.nodes.load_context import load_context_node
from changetools.agents.generation.nodes.persist import persist_node
from changetools.agents.generation.nodes.retrieve_evidence import retrieve_evidence_node
from changetools.agents.generation.nodes.validate import (
    should_retry_after_validation,
    validate_node,
)

__all__ = [
    "assemble_node",
    "cite_evidence_node",
    "detect_conflicts_node",
    "draft_sections_node",
    "load_context_node",
    "persist_node",
    "retrieve_evidence_node",
    "should_retry_after_validation",
    "validate_node",
]
