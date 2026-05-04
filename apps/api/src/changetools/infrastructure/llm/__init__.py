"""LLM provider abstraction.

Public API:
    - ``LLMProvider``  — Protocol the rest of the app depends on
    - ``ChatMessage``  — typed message tuple (role + content)
    - ``build_llm_provider`` — factory that returns the configured provider
"""

from changetools.infrastructure.llm.base import (
    ChatMessage,
    ChatResponse,
    LLMProvider,
)
from changetools.infrastructure.llm.factory import build_llm_provider

__all__ = [
    "ChatMessage",
    "ChatResponse",
    "LLMProvider",
    "build_llm_provider",
]
