"""Claude AI client adapter.

Implements AIClientPort using Anthropic's Claude API.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from meal_planning.services.ports.ai_client import AIMessage, AIResponse

if TYPE_CHECKING:
    pass


class ClaudeClient:
    """Claude API client implementing AIClientPort.

    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-3-haiku-20240307",
    ):
        """Initialize Claude client.

        Args:
            api_key: API key. Defaults to ANTHROPIC_API_KEY env var.
            model: Model to use.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self._client = None

    def _get_client(self):
        """Lazy initialize Anthropic client."""
        if self._client is None:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic package required. Install with: pip install anthropic"
                )
        return self._client

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
        client = self._get_client()

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)

        return AIResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

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
        client = self._get_client()

        api_messages = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": api_messages,
        }
        if system:
            kwargs["system"] = system

        response = client.messages.create(**kwargs)

        return AIResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )
