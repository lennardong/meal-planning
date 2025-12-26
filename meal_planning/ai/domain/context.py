"""AI Context domain model.

VOAIContext stores user preferences and constraints that guide AI decisions.
"""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


def _context_uid() -> str:
    """Generate unique context identifier."""
    return f"CTX-{uuid4().hex[:8]}"


class VOAIContext(BaseModel):
    """Immutable AI context value object.

    Stores user preferences that influence AI meal planning decisions.
    Examples:
    - Dietary: "Vegetarian, no eggs, prefer Asian cuisines"
    - Location: "Located in Johor Bahru, prefer local ingredients"
    - Budget: "Cooking for 2 adults, budget-conscious"
    """

    model_config = ConfigDict(frozen=True)

    uid: str = Field(default_factory=_context_uid)
    category: str | None = None  # e.g., "dietary", "location", "budget"
    context: str  # Natural language description

    def with_context(self, context: str) -> VOAIContext:
        """Return new context with updated description."""
        return self.model_copy(update={"context": context})

    def with_category(self, category: str) -> VOAIContext:
        """Return new context with updated category."""
        return self.model_copy(update={"category": category})
