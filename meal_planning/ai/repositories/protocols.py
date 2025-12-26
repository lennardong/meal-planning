"""AI repository protocols."""

from __future__ import annotations

from typing import Protocol, Sequence

from meal_planning.shared.types import Result, NotFoundError, DuplicateError
from meal_planning.ai.domain.context import VOAIContext


class AIContextRepository(Protocol):
    """Repository protocol for AI contexts."""

    def add(self, context: VOAIContext) -> Result[VOAIContext, DuplicateError]:
        """Add a new context."""
        ...

    def get(self, uid: str) -> Result[VOAIContext, NotFoundError]:
        """Get context by uid."""
        ...

    def list_all(self) -> Sequence[VOAIContext]:
        """List all contexts."""
        ...

    def find_by_category(self, category: str) -> Sequence[VOAIContext]:
        """Find contexts by category."""
        ...

    def update(self, context: VOAIContext) -> Result[VOAIContext, NotFoundError]:
        """Update an existing context."""
        ...

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete context by uid."""
        ...
