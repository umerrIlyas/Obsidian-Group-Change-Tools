"""Versioned prompts for the agent pipeline.

Prompts are kept here (not inlined in nodes) so they can be diffed and
regression-tested without touching the graph code. Each prompt module
declares ``VERSION`` so eval reports can be tied to a specific revision.
"""
