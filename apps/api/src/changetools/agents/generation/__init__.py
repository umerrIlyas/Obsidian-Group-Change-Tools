"""Brief-generation graph.

A LangGraph state machine that turns a project's ingested chunks into a
validated Change Strategy Brief. Each step is a separate function so traces
in LangSmith correspond 1:1 to the pipeline stages.
"""

from changetools.agents.generation.graph import build_generation_graph
from changetools.agents.generation.state import (
    SECTION_NAMES,
    GenerationState,
    ProgressEvent,
    SectionName,
)

__all__ = [
    "SECTION_NAMES",
    "GenerationState",
    "ProgressEvent",
    "SectionName",
    "build_generation_graph",
]
