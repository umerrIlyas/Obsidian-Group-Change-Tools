"""LLM provider Protocol + shared types.

Every concrete provider returns an instance of ``langchain_core.language_models.BaseChatModel``
so the rest of the app can use the LangChain runtime (structured output, tool calling,
streaming) regardless of vendor.
"""

from __future__ import annotations

from typing import Literal, Protocol

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel

Role = Literal["system", "user", "assistant", "tool"]


class ChatMessage(BaseModel):
    role: Role
    content: str


class ChatResponse(BaseModel):
    content: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMProvider(Protocol):
    """Adapter around a single LLM vendor.

    The provider exposes a configured LangChain chat model so the rest of the app
    can use idiomatic LangChain features (`with_structured_output`, tool binding,
    streaming) without coupling to a specific vendor SDK.
    """

    name: str
    model: str

    def chat_model(
        self,
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> BaseChatModel:
        """Return a configured chat model. Cheap to call; cache at the consumer."""
        ...
