"""Catalogue aggregate root.

The Catalogue aggregate manages dishes with their categories.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from meal_planning.core.catalogue.models import Dish


@dataclass
class Catalogue:
    """Aggregate root for dishes.

    Dishes are keyed by UID (entity pattern).
    Categories are stored directly on each dish.
    """

    _dishes: dict[str, Dish] = field(default_factory=dict)

    # --- Dishes (keyed by UID) ---

    def add_dish(self, dish: Dish) -> Dish:
        """Add dish to catalogue. Returns the added dish."""
        self._dishes[dish.uid] = dish
        return dish

    def get_dish(self, uid: str) -> Dish | None:
        """Get dish by UID."""
        return self._dishes.get(uid)

    def get_dish_by_name(self, name: str) -> Dish | None:
        """Get dish by name (case-insensitive)."""
        name_normalized = name.strip().title()
        for dish in self._dishes.values():
            if dish.name == name_normalized:
                return dish
        return None

    def all_dishes(self) -> list[Dish]:
        """Get all dishes."""
        return list(self._dishes.values())

    def remove_dish(self, uid: str) -> bool:
        """Remove dish. Returns True if removed."""
        if uid in self._dishes:
            del self._dishes[uid]
            return True
        return False

    def count(self) -> int:
        """Return number of dishes."""
        return len(self._dishes)
