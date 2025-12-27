"""Catalogue service - manages dishes.

This service handles:
- Loading/saving dishes from blob storage
- JSON serialization/deserialization
- User-scoped key construction
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.shared.types import Result, Ok, Err, NotFoundError, DuplicateError

if TYPE_CHECKING:
    from meal_planning.services.ports.blobstore import BlobStore


class CatalogueService:
    """Manages dishes with JSON persistence."""

    def __init__(self, store: BlobStore, user_id: str = "default"):
        """Initialize the catalogue service.

        Args:
            store: Blob store for persistence.
            user_id: User identifier for data scoping.
        """
        self._store = store
        self._user_id = user_id
        self._dishes: dict[str, Dish] = {}
        self._loaded = False

    def _key(self, filename: str) -> str:
        """Construct blob key with user scoping."""
        return f"{self._user_id}/{filename}"

    def _ensure_loaded(self) -> None:
        """Lazy load data from store, falling back to defaults for new users."""
        if self._loaded:
            return

        # Load dishes from user storage
        dish_bytes = self._store.load_blob(self._key("dishes.json"))
        if dish_bytes:
            dish_data = json.loads(dish_bytes.decode("utf-8"))
            self._dishes = {
                uid: Dish.model_validate(data)
                for uid, data in dish_data.items()
            }
        else:
            # No user data - use defaults (lazy, don't persist yet)
            from meal_planning.core.catalogue.defaults import DEFAULT_DISHES

            self._dishes = {d.uid: d for d in DEFAULT_DISHES}

        self._loaded = True

    def save(self) -> None:
        """Persist all data to blob store."""
        # Save dishes
        dish_data = {uid: dish.model_dump() for uid, dish in self._dishes.items()}
        self._store.save_blob(
            self._key("dishes.json"),
            json.dumps(dish_data, indent=2).encode("utf-8"),
        )

    # Dish operations

    def add_dish(self, dish: Dish) -> Result[Dish, DuplicateError]:
        """Add a new dish.

        Args:
            dish: Dish to add.

        Returns:
            Ok(dish) if added, Err if duplicate.
        """
        self._ensure_loaded()
        if dish.uid in self._dishes:
            return Err(DuplicateError("Dish", dish.uid))
        self._dishes[dish.uid] = dish
        return Ok(dish)

    def get_dish(self, uid: str) -> Result[Dish, NotFoundError]:
        """Get a dish by UID.

        Args:
            uid: Dish UID.

        Returns:
            Ok(dish) if found, Err if not found.
        """
        self._ensure_loaded()
        dish = self._dishes.get(uid)
        if dish is None:
            return Err(NotFoundError("Dish", uid))
        return Ok(dish)

    def get_dish_by_name(self, name: str) -> Result[Dish, NotFoundError]:
        """Get a dish by name (case-insensitive).

        Args:
            name: Dish name.

        Returns:
            Ok(dish) if found, Err if not found.
        """
        self._ensure_loaded()
        name_normalized = name.strip().title()
        for dish in self._dishes.values():
            if dish.name == name_normalized:
                return Ok(dish)
        return Err(NotFoundError("Dish", name))

    def list_dishes(self) -> list[Dish]:
        """Get all dishes."""
        self._ensure_loaded()
        return list(self._dishes.values())

    def update_dish(self, dish: Dish) -> Result[Dish, NotFoundError]:
        """Update an existing dish.

        Args:
            dish: Updated dish.

        Returns:
            Ok(dish) if updated, Err if not found.
        """
        self._ensure_loaded()
        if dish.uid not in self._dishes:
            return Err(NotFoundError("Dish", dish.uid))
        self._dishes[dish.uid] = dish
        return Ok(dish)

    def delete_dish(self, uid: str) -> Result[None, NotFoundError]:
        """Delete a dish.

        Args:
            uid: Dish UID.

        Returns:
            Ok(None) if deleted, Err if not found.
        """
        self._ensure_loaded()
        if uid not in self._dishes:
            return Err(NotFoundError("Dish", uid))
        del self._dishes[uid]
        return Ok(None)

    def reset_to_defaults(self, keep_user_additions: bool = True) -> int:
        """Reset catalogue to default dishes.

        Args:
            keep_user_additions: If True, keeps user-created dishes (non-default).

        Returns:
            Number of dishes after reset.
        """
        from meal_planning.core.catalogue.defaults import DEFAULT_DISHES, is_default_dish

        self._ensure_loaded()

        if keep_user_additions:
            # Keep only user-created dishes (those without DEFAULT- prefix)
            user_dishes = {
                uid: d for uid, d in self._dishes.items() if not is_default_dish(uid)
            }
        else:
            user_dishes = {}

        # Merge defaults with user dishes (user dishes take precedence if same UID)
        self._dishes = {d.uid: d for d in DEFAULT_DISHES} | user_dishes
        self.save()
        return len(self._dishes)
