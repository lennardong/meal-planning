"""Unified Store for accessing all repositories.

This module provides the Store dataclass that aggregates all repositories
and a context manager for managing the JSON persistence lifecycle.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Generator

from meal_planning.shared.persistence.json_store import JsonStore
from meal_planning.catalogue.repositories.json_repos import (
    JsonIngredientRepository,
    JsonDishRepository,
)
from meal_planning.planning.repositories.json_repos import JsonPlanRepository
from meal_planning.ai.repositories.json_repos import JsonAIContextRepository


@dataclass
class Store:
    """Unified access to all repositories.

    Aggregates all repositories for convenient access.
    Used by the agent and CLI for all data operations.
    """

    ingredients: JsonIngredientRepository
    dishes: JsonDishRepository
    plans: JsonPlanRepository
    ai_contexts: JsonAIContextRepository
    _json_store: JsonStore

    def save(self) -> None:
        """Explicitly save all data to disk."""
        self._json_store.save()

    def reload(self) -> None:
        """Reload data from disk, discarding unsaved changes."""
        self._json_store.reload()


@contextmanager
def store(path: Path | str = Path("data/meals.json")) -> Generator[Store, None, None]:
    """Context manager for Store with automatic save on exit.

    Usage:
        with store() as s:
            s.ingredients.add(ingredient)
            s.dishes.add(dish)
        # Automatically saved on exit

    Args:
        path: Path to JSON data file.

    Yields:
        Store instance with all repositories.
    """
    if isinstance(path, str):
        path = Path(path)

    json_store = JsonStore(path)

    yield Store(
        ingredients=JsonIngredientRepository(json_store),
        dishes=JsonDishRepository(json_store),
        plans=JsonPlanRepository(json_store),
        ai_contexts=JsonAIContextRepository(json_store),
        _json_store=json_store,
    )

    json_store.save()


def create_store(path: Path | str = Path("data/meals.json")) -> Store:
    """Create a Store without context manager.

    Use this when you need manual control over save timing.
    Remember to call store.save() when done!

    Args:
        path: Path to JSON data file.

    Returns:
        Store instance.
    """
    if isinstance(path, str):
        path = Path(path)

    json_store = JsonStore(path)

    return Store(
        ingredients=JsonIngredientRepository(json_store),
        dishes=JsonDishRepository(json_store),
        plans=JsonPlanRepository(json_store),
        ai_contexts=JsonAIContextRepository(json_store),
        _json_store=json_store,
    )
