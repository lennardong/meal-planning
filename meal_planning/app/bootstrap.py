"""Application bootstrap and dependency injection.

Wire up all dependencies and create the application context.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from meal_planning.app.store import Store, create_store
from meal_planning.ai.agent import MealPlanningAgent


@dataclass
class AppContext:
    """Application context with all dependencies wired up.

    Provides access to the store and agent for CLI and other consumers.
    """

    store: Store
    agent: MealPlanningAgent

    def save(self) -> None:
        """Save all data to disk."""
        self.store.save()


@contextmanager
def create_app(
    data_path: Path | str = Path("data/meals.json"),
) -> Generator[AppContext, None, None]:
    """Create application context with automatic save on exit.

    This is the main entry point for the application.
    Wires up all dependencies and provides a context manager.

    Usage:
        with create_app() as ctx:
            ctx.agent.schedule_dish(...)
            print(ctx.agent.get_plan_summary("2025-01"))
        # Automatically saved on exit

    Args:
        data_path: Path to JSON data file.

    Yields:
        AppContext with store and agent.
    """
    if isinstance(data_path, str):
        data_path = Path(data_path)

    # Create store
    store = create_store(data_path)

    # Load AI contexts
    contexts = store.ai_contexts.list_all()

    # Create agent
    agent = MealPlanningAgent(
        store=store,
        contexts=contexts,
        client=None,  # No AI client for now
    )

    yield AppContext(store=store, agent=agent)

    # Save on exit
    store.save()


def create_app_no_context(
    data_path: Path | str = Path("data/meals.json"),
) -> AppContext:
    """Create application context without context manager.

    Use this when you need manual control over lifecycle.
    Remember to call ctx.save() when done!

    Args:
        data_path: Path to JSON data file.

    Returns:
        AppContext instance.
    """
    if isinstance(data_path, str):
        data_path = Path(data_path)

    store = create_store(data_path)
    contexts = store.ai_contexts.list_all()

    agent = MealPlanningAgent(
        store=store,
        contexts=contexts,
        client=None,
    )

    return AppContext(store=store, agent=agent)
