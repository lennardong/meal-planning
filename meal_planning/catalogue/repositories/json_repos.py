"""JSON implementations of catalogue repositories.

These repositories operate on in-memory data from JsonStore.
"""

from __future__ import annotations

from typing import Sequence

from meal_planning.shared.types import Result, Ok, Err, NotFoundError, DuplicateError
from meal_planning.shared.persistence.json_store import JsonStore
from meal_planning.catalogue.domain.models import VOIngredient, VODish
from meal_planning.catalogue.domain.enums import IngredientTag, DishTag


class JsonIngredientRepository:
    """JSON-backed ingredient repository."""

    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def add(self, ingredient: VOIngredient) -> Result[VOIngredient, DuplicateError]:
        """Add a new ingredient to the bank."""
        if ingredient.uid in self._store.ingredient_bank:
            return Err(DuplicateError(entity="Ingredient", uid=ingredient.uid))

        self._store.ingredient_bank[ingredient.uid] = ingredient.model_dump(mode="json")
        return Ok(ingredient)

    def get(self, uid: str) -> Result[VOIngredient, NotFoundError]:
        """Get ingredient by uid."""
        if uid not in self._store.ingredient_bank:
            return Err(NotFoundError(entity="Ingredient", uid=uid))

        return Ok(VOIngredient.model_validate(self._store.ingredient_bank[uid]))

    def get_by_name(self, name: str) -> Result[VOIngredient, NotFoundError]:
        """Get ingredient by name (case-insensitive)."""
        name_lower = name.lower()
        for data in self._store.ingredient_bank.values():
            if data["name"].lower() == name_lower:
                return Ok(VOIngredient.model_validate(data))

        return Err(NotFoundError(entity="Ingredient", uid=f"name:{name}"))

    def list_all(self) -> Sequence[VOIngredient]:
        """List all ingredients."""
        return [
            VOIngredient.model_validate(data)
            for data in self._store.ingredient_bank.values()
        ]

    def find_by_tag(self, tag: IngredientTag) -> Sequence[VOIngredient]:
        """Find all ingredients with a specific tag."""
        results = []
        for data in self._store.ingredient_bank.values():
            if tag.value in data.get("tags", []):
                results.append(VOIngredient.model_validate(data))
        return results

    def update(self, ingredient: VOIngredient) -> Result[VOIngredient, NotFoundError]:
        """Update an existing ingredient."""
        if ingredient.uid not in self._store.ingredient_bank:
            return Err(NotFoundError(entity="Ingredient", uid=ingredient.uid))

        self._store.ingredient_bank[ingredient.uid] = ingredient.model_dump(mode="json")
        return Ok(ingredient)

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete ingredient by uid."""
        if uid not in self._store.ingredient_bank:
            return Err(NotFoundError(entity="Ingredient", uid=uid))

        del self._store.ingredient_bank[uid]
        return Ok(None)


class JsonDishRepository:
    """JSON-backed dish repository."""

    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def add(self, dish: VODish) -> Result[VODish, DuplicateError]:
        """Add a new dish to the bank."""
        if dish.uid in self._store.dish_bank:
            return Err(DuplicateError(entity="Dish", uid=dish.uid))

        self._store.dish_bank[dish.uid] = dish.model_dump(mode="json")
        return Ok(dish)

    def get(self, uid: str) -> Result[VODish, NotFoundError]:
        """Get dish by uid."""
        if uid not in self._store.dish_bank:
            return Err(NotFoundError(entity="Dish", uid=uid))

        return Ok(VODish.model_validate(self._store.dish_bank[uid]))

    def get_by_name(self, name: str) -> Result[VODish, NotFoundError]:
        """Get dish by name (case-insensitive)."""
        name_lower = name.lower()
        for data in self._store.dish_bank.values():
            if data["name"].lower() == name_lower:
                return Ok(VODish.model_validate(data))

        return Err(NotFoundError(entity="Dish", uid=f"name:{name}"))

    def list_all(self) -> Sequence[VODish]:
        """List all dishes."""
        return [VODish.model_validate(data) for data in self._store.dish_bank.values()]

    def find_by_tag(self, tag: DishTag) -> Sequence[VODish]:
        """Find all dishes with a specific tag."""
        results = []
        for data in self._store.dish_bank.values():
            if tag.value in data.get("tags", []):
                results.append(VODish.model_validate(data))
        return results

    def find_by_ingredient(self, ingredient_uid: str) -> Sequence[VODish]:
        """Find all dishes containing a specific ingredient."""
        results = []
        for data in self._store.dish_bank.values():
            if ingredient_uid in data.get("ingredient_uids", []):
                results.append(VODish.model_validate(data))
        return results

    def update(self, dish: VODish) -> Result[VODish, NotFoundError]:
        """Update an existing dish."""
        if dish.uid not in self._store.dish_bank:
            return Err(NotFoundError(entity="Dish", uid=dish.uid))

        self._store.dish_bank[dish.uid] = dish.model_dump(mode="json")
        return Ok(dish)

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete dish by uid."""
        if uid not in self._store.dish_bank:
            return Err(NotFoundError(entity="Dish", uid=uid))

        del self._store.dish_bank[uid]
        return Ok(None)
