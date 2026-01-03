"""Application bootstrap - wires adapters, services, and API together.

This module provides:
- Application context creation
- Dependency injection wiring
- Global context management for CLI
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from meal_planning.infra.config import get_data_path, get_user_id
from meal_planning.infra.stores.local_filesystem import LocalFilesystemBlobStore
from meal_planning.infra.stores.migration import migrate_if_needed
from meal_planning.services.ai_assistant import AIAssistantService
from meal_planning.services.analysis import AnalysisService
from meal_planning.services.catalogue import CatalogueService
from meal_planning.services.context import ContextService
from meal_planning.services.planning import PlanningService

if TYPE_CHECKING:
    from meal_planning.services.ports.ai_client import AIClientPort


@dataclass
class AppContext:
    """Application context containing all services."""

    catalogue: CatalogueService
    planning: PlanningService
    context: ContextService
    analysis: AnalysisService
    ai_assistant: AIAssistantService


# Global context for CLI usage
_app_context: AppContext | None = None


def create_app_context(
    data_path: Path | None = None,
    user_id: str | None = None,
    ai_client: "AIClientPort | None" = None,
    auto_migrate: bool = True,
) -> AppContext:
    """Create application context with all services wired up.

    Args:
        data_path: Path for data storage. Defaults to config value.
        user_id: User identifier. Defaults to config value.
        ai_client: Optional AI client for AI features.
        auto_migrate: Whether to auto-migrate old data format.

    Returns:
        AppContext with all services initialized.
    """
    # Use defaults from config if not provided
    data_path = (
        data_path or get_data_path()
    )  # TODO this feels to magical. we should expect it in args and/or set a default there, not bury this here
    # TODO similar fo rother bootstrapping funcs. I prefer explicit over implicity with sensiblle defaults
    user_id = user_id or get_user_id()

    # Auto-migrate if needed
    if auto_migrate:
        migrate_if_needed(data_path, user_id)

    # Create infrastructure adapters
    store = LocalFilesystemBlobStore(data_path)

    # Create services with injected adapters
    catalogue = CatalogueService(store, user_id)
    planning = PlanningService(store, user_id)
    context = ContextService(store, user_id)

    # Create orchestrating services
    analysis = AnalysisService(catalogue, planning)
    ai_assistant = AIAssistantService(catalogue, planning, context, ai_client)

    return AppContext(
        catalogue=catalogue,
        planning=planning,
        context=context,
        analysis=analysis,
        ai_assistant=ai_assistant,
    )


def initialize_app(
    data_path: Path | None = None,
    user_id: str | None = None,
    ai_client: "AIClientPort | None" = None,
) -> AppContext:
    """Initialize the global application context.

    This is called at CLI startup to set up the global context
    that command handlers can access via get_app_context().

    Args:
        data_path: Path for data storage.
        user_id: User identifier.
        ai_client: Optional AI client.

    Returns:
        Initialized AppContext.
    """
    global _app_context
    _app_context = create_app_context(data_path, user_id, ai_client)
    return _app_context


def get_app_context() -> AppContext:
    """Get the global application context.

    Used by CLI commands to access services.

    Returns:
        AppContext.

    Raises:
        RuntimeError: If app not initialized.
    """
    global _app_context
    if _app_context is None:
        # Auto-initialize with defaults if not already done
        _app_context = create_app_context()
    return _app_context


def reset_app_context() -> None:
    """Reset the global context. Useful for testing."""
    global _app_context
    _app_context = None


# =============================================================================
# Multi-User Session Management
# =============================================================================


class AppContextManager:
    """Manages per-user application contexts for multi-user support.

    Each user session gets its own isolated context with separate data.
    New users automatically get a copy of the default dishes.
    """

    def __init__(self):
        self._contexts: dict[str, AppContext] = {}

    def get_context(self, user_id: str) -> AppContext:
        """Get or create context for a user.

        Args:
            user_id: User's session ID.

        Returns:
            AppContext for the user.
        """
        if user_id not in self._contexts:
            ctx = create_app_context(user_id=user_id)
            # Copy default dishes for new users
            if not ctx.catalogue.list_dishes():
                self._copy_default_dishes(ctx)
            self._contexts[user_id] = ctx
        return self._contexts[user_id]

    def _copy_default_dishes(self, ctx: AppContext) -> None:
        """Copy dishes from default catalogue to new user."""
        default_ctx = create_app_context(user_id="default")
        for dish in default_ctx.catalogue.list_dishes():
            ctx.catalogue.add_dish(dish)
        ctx.catalogue.save()


_context_manager = AppContextManager()


def get_user_context(user_id: str) -> AppContext:
    """Get context for a specific user session.

    Args:
        user_id: User's session ID (from browser localStorage).

    Returns:
        AppContext isolated to that user.
    """
    return _context_manager.get_context(user_id)
