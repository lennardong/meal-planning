"""JSON implementations of AI repositories."""

from __future__ import annotations

from typing import Sequence

from meal_planning.shared.types import Result, Ok, Err, NotFoundError, DuplicateError
from meal_planning.shared.persistence.json_store import JsonStore
from meal_planning.ai.domain.context import VOAIContext


class JsonAIContextRepository:
    """JSON-backed AI context repository."""

    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def add(self, context: VOAIContext) -> Result[VOAIContext, DuplicateError]:
        """Add a new context."""
        if context.uid in self._store.ai_context_bank:
            return Err(DuplicateError(entity="AIContext", uid=context.uid))

        self._store.ai_context_bank[context.uid] = context.model_dump(mode="json")
        return Ok(context)

    def get(self, uid: str) -> Result[VOAIContext, NotFoundError]:
        """Get context by uid."""
        if uid not in self._store.ai_context_bank:
            return Err(NotFoundError(entity="AIContext", uid=uid))

        return Ok(VOAIContext.model_validate(self._store.ai_context_bank[uid]))

    def list_all(self) -> Sequence[VOAIContext]:
        """List all contexts."""
        return [
            VOAIContext.model_validate(data)
            for data in self._store.ai_context_bank.values()
        ]

    def find_by_category(self, category: str) -> Sequence[VOAIContext]:
        """Find contexts by category."""
        results = []
        for data in self._store.ai_context_bank.values():
            if data.get("category") == category:
                results.append(VOAIContext.model_validate(data))
        return results

    def update(self, context: VOAIContext) -> Result[VOAIContext, NotFoundError]:
        """Update an existing context."""
        if context.uid not in self._store.ai_context_bank:
            return Err(NotFoundError(entity="AIContext", uid=context.uid))

        self._store.ai_context_bank[context.uid] = context.model_dump(mode="json")
        return Ok(context)

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete context by uid."""
        if uid not in self._store.ai_context_bank:
            return Err(NotFoundError(entity="AIContext", uid=uid))

        del self._store.ai_context_bank[uid]
        return Ok(None)

    def get_all_context_text(self) -> str:
        """Combine all contexts into single text for AI prompts."""
        contexts = self.list_all()
        if not contexts:
            return ""

        parts = []
        for ctx in contexts:
            if ctx.category:
                parts.append(f"[{ctx.category}] {ctx.context}")
            else:
                parts.append(ctx.context)

        return "\n".join(parts)
