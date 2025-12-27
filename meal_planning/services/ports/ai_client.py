"""AI Client port - abstraction for AI interactions.

The AIClientPort defines the interface for AI-powered features
like meal suggestions and chat interactions.

Implementations:
- ClaudeClient (infra/ai/claude_client.py)
"""

from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class AIMessage:
    """A message in an AI conversation."""

    role: str  # "user" or "assistant"
    content: str


@dataclass(frozen=True)
class AIResponse:
    """Response from an AI query."""

    content: str
    model: str
    usage: dict[str, int] | None = None


class AIClientPort(Protocol):
    """Port for AI client interactions.

    Abstracts the underlying AI provider (Claude, OpenAI, etc.).
    """

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Get a completion for a single prompt.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.
            max_tokens: Maximum tokens in response.

        Returns:
            AIResponse with the completion.
        """
        ...

    def chat(
        self,
        messages: list[AIMessage],
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> AIResponse:
        """Continue a multi-turn conversation.

        Args:
            messages: Conversation history.
            system: Optional system prompt.
            max_tokens: Maximum tokens in response.

        Returns:
            AIResponse with the next message.
        """
        ...
