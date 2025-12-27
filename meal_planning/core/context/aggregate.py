"""Preferences aggregate root.

The Preferences aggregate manages user contexts that guide AI decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from meal_planning.core.context.models import UserContext


@dataclass
class Preferences:
    """Aggregate root for user contexts.

    Manages user preferences like dietary restrictions, location,
    and budget constraints that influence meal planning.
    """

    _contexts: dict[str, UserContext] = field(default_factory=dict)

    def add(self, context: UserContext) -> UserContext:
        """Add context to preferences. Returns the added context."""
        self._contexts[context.uid] = context
        return context

    def get(self, uid: str) -> UserContext | None:
        """Get context by UID."""
        return self._contexts.get(uid)

    def get_by_category(self, category: str) -> list[UserContext]:
        """Get all contexts in a category."""
        return [
            ctx for ctx in self._contexts.values()
            if ctx.category == category
        ]

    def all(self) -> list[UserContext]:
        """Get all contexts."""
        return list(self._contexts.values())

    def remove(self, uid: str) -> bool:
        """Remove context. Returns True if removed."""
        if uid in self._contexts:
            del self._contexts[uid]
            return True
        return False

    def all_text(self) -> str:
        """Combine all contexts into a single text for AI prompts.

        Groups by category for better prompt structure.
        """
        if not self._contexts:
            return ""

        # Group by category
        by_category: dict[str | None, list[str]] = {}
        for ctx in self._contexts.values():
            cat = ctx.category or "general"
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(ctx.context)

        # Format as text
        parts = []
        for cat, texts in sorted(by_category.items(), key=lambda x: x[0] or ""):
            parts.append(f"{cat.title()}: {'; '.join(texts)}")

        return "\n".join(parts)

    def count(self) -> int:
        """Return number of contexts."""
        return len(self._contexts)
