"""Context service - manages user contexts.

This service handles:
- Loading/saving user contexts from blob storage
- JSON serialization/deserialization
- User-scoped key construction
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from meal_planning.core.context.models import VOUserContext
from meal_planning.core.shared.types import Result, Ok, Err, NotFoundError, DuplicateError

if TYPE_CHECKING:
    from meal_planning.services.ports.blobstore import BlobStore


class ContextService:
    """Manages user contexts with JSON persistence."""

    def __init__(self, store: BlobStore, user_id: str = "default"):
        """Initialize the context service.

        Args:
            store: Blob store for persistence.
            user_id: User identifier for data scoping.
        """
        self._store = store
        self._user_id = user_id
        self._contexts: dict[str, VOUserContext] = {}
        self._loaded = False

    def _key(self, filename: str) -> str:
        """Construct blob key with user scoping."""
        return f"{self._user_id}/{filename}"

    def _ensure_loaded(self) -> None:
        """Lazy load data from store."""
        if self._loaded:
            return

        ctx_bytes = self._store.load_blob(self._key("contexts.json"))
        if ctx_bytes:
            ctx_data = json.loads(ctx_bytes.decode("utf-8"))
            self._contexts = {
                uid: VOUserContext.model_validate(data)
                for uid, data in ctx_data.items()
            }

        self._loaded = True

    def save(self) -> None:
        """Persist all data to blob store."""
        ctx_data = {uid: ctx.model_dump() for uid, ctx in self._contexts.items()}
        self._store.save_blob(
            self._key("contexts.json"),
            json.dumps(ctx_data, indent=2).encode("utf-8"),
        )

    def add_context(
        self, context: VOUserContext
    ) -> Result[VOUserContext, DuplicateError]:
        """Add a new context.

        Args:
            context: Context to add.

        Returns:
            Ok(context) if added, Err if duplicate.
        """
        self._ensure_loaded()
        if context.uid in self._contexts:
            return Err(DuplicateError("Context", context.uid))
        self._contexts[context.uid] = context
        return Ok(context)

    def get_context(self, uid: str) -> Result[VOUserContext, NotFoundError]:
        """Get a context by UID.

        Args:
            uid: Context UID.

        Returns:
            Ok(context) if found, Err if not found.
        """
        self._ensure_loaded()
        ctx = self._contexts.get(uid)
        if ctx is None:
            return Err(NotFoundError("Context", uid))
        return Ok(ctx)

    def list_contexts(self) -> list[VOUserContext]:
        """Get all contexts."""
        self._ensure_loaded()
        return list(self._contexts.values())

    def list_contexts_by_category(self, category: str) -> list[VOUserContext]:
        """Get contexts by category.

        Args:
            category: Category to filter by.

        Returns:
            List of matching contexts.
        """
        self._ensure_loaded()
        return [ctx for ctx in self._contexts.values() if ctx.category == category]

    def update_context(
        self, context: VOUserContext
    ) -> Result[VOUserContext, NotFoundError]:
        """Update an existing context.

        Args:
            context: Updated context.

        Returns:
            Ok(context) if updated, Err if not found.
        """
        self._ensure_loaded()
        if context.uid not in self._contexts:
            return Err(NotFoundError("Context", context.uid))
        self._contexts[context.uid] = context
        return Ok(context)

    def delete_context(self, uid: str) -> Result[None, NotFoundError]:
        """Delete a context.

        Args:
            uid: Context UID.

        Returns:
            Ok(None) if deleted, Err if not found.
        """
        self._ensure_loaded()
        if uid not in self._contexts:
            return Err(NotFoundError("Context", uid))
        del self._contexts[uid]
        return Ok(None)

    def get_all_context_text(self) -> str:
        """Get all context texts combined for AI prompts.

        Returns:
            Combined context string.
        """
        self._ensure_loaded()
        if not self._contexts:
            return ""
        return "\n".join(ctx.context for ctx in self._contexts.values())
