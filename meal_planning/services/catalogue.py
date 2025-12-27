"""Catalogue service - manages ingredients and dishes.

This service handles:
- Loading/saving ingredients and dishes from blob storage
- JSON serialization/deserialization
- User-scoped key construction
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from meal_planning.core.catalogue.models import VOIngredient, VODish
from meal_planning.core.shared.types import Result, Ok, Err, NotFoundError, DuplicateError

if TYPE_CHECKING:
    from meal_planning.services.ports.blobstore import BlobStore


class CatalogueService:
    """Manages ingredients and dishes with JSON persistence."""

    def __init__(self, store: BlobStore, user_id: str = "default"):
        """Initialize the catalogue service.

        Args:
            store: Blob store for persistence.
            user_id: User identifier for data scoping.
        """
        self._store = store
        self._user_id = user_id
        self._ingredients: dict[str, VOIngredient] = {}
        self._dishes: dict[str, VODish] = {}
        self._loaded = False

    def _key(self, filename: str) -> str:
        """Construct blob key with user scoping."""
        return f"{self._user_id}/{filename}"

    def _ensure_loaded(self) -> None:
        """Lazy load data from store."""
        if self._loaded:
            return

        # Load ingredients
        ing_bytes = self._store.load_blob(self._key("ingredients.json"))
        if ing_bytes:
            ing_data = json.loads(ing_bytes.decode("utf-8"))
            self._ingredients = {
                uid: VOIngredient.model_validate(data)
                for uid, data in ing_data.items()
            }

        # Load dishes
        dish_bytes = self._store.load_blob(self._key("dishes.json"))
        if dish_bytes:
            dish_data = json.loads(dish_bytes.decode("utf-8"))
            self._dishes = {
                uid: VODish.model_validate(data)
                for uid, data in dish_data.items()
            }

        self._loaded = True

    def save(self) -> None:
        """Persist all data to blob store."""
        # Save ingredients
        ing_data = {uid: ing.model_dump() for uid, ing in self._ingredients.items()}
        self._store.save_blob(
            self._key("ingredients.json"),
            json.dumps(ing_data, indent=2).encode("utf-8"),
        )

        # Save dishes
        dish_data = {uid: dish.model_dump() for uid, dish in self._dishes.items()}
        self._store.save_blob(
            self._key("dishes.json"),
            json.dumps(dish_data, indent=2).encode("utf-8"),
        )

    # Ingredient operations

    def add_ingredient(
        self, ingredient: VOIngredient
    ) -> Result[VOIngredient, DuplicateError]:
        """Add a new ingredient.

        Args:
            ingredient: Ingredient to add.

        Returns:
            Ok(ingredient) if added, Err if duplicate.
        """
        self._ensure_loaded()
        if ingredient.uid in self._ingredients:
            return Err(DuplicateError("Ingredient", ingredient.uid))
        self._ingredients[ingredient.uid] = ingredient
        return Ok(ingredient)

    def get_ingredient(self, uid: str) -> Result[VOIngredient, NotFoundError]:
        """Get an ingredient by UID.

        Args:
            uid: Ingredient UID.

        Returns:
            Ok(ingredient) if found, Err if not found.
        """
        self._ensure_loaded()
        ing = self._ingredients.get(uid)
        if ing is None:
            return Err(NotFoundError("Ingredient", uid))
        return Ok(ing)

    def list_ingredients(self) -> list[VOIngredient]:
        """Get all ingredients."""
        self._ensure_loaded()
        return list(self._ingredients.values())

    def update_ingredient(
        self, ingredient: VOIngredient
    ) -> Result[VOIngredient, NotFoundError]:
        """Update an existing ingredient.

        Args:
            ingredient: Updated ingredient.

        Returns:
            Ok(ingredient) if updated, Err if not found.
        """
        self._ensure_loaded()
        if ingredient.uid not in self._ingredients:
            return Err(NotFoundError("Ingredient", ingredient.uid))
        self._ingredients[ingredient.uid] = ingredient
        return Ok(ingredient)

    def delete_ingredient(self, uid: str) -> Result[None, NotFoundError]:
        """Delete an ingredient.

        Args:
            uid: Ingredient UID.

        Returns:
            Ok(None) if deleted, Err if not found.
        """
        self._ensure_loaded()
        if uid not in self._ingredients:
            return Err(NotFoundError("Ingredient", uid))
        del self._ingredients[uid]
        return Ok(None)

    # Dish operations

    def add_dish(self, dish: VODish) -> Result[VODish, DuplicateError]:
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

    def get_dish(self, uid: str) -> Result[VODish, NotFoundError]:
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

    def list_dishes(self) -> list[VODish]:
        """Get all dishes."""
        self._ensure_loaded()
        return list(self._dishes.values())

    def update_dish(self, dish: VODish) -> Result[VODish, NotFoundError]:
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
