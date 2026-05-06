"""Refinement chat agent.

A LangGraph ReAct agent that lets users refine the brief and deck through
natural-language requests. Tools provide read/write access to the brief,
retrieval over the source docs, and deck regeneration.
"""

from changetools.agents.refinement.graph import build_refinement_agent

__all__ = ["build_refinement_agent"]
