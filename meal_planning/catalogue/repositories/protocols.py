"""Catalogue repository protocols.

Defines abstract interfaces for ingredient and dish storage.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from meal_planning.shared.types import Result, NotFoundError, DuplicateError
from meal_planning.catalogue.domain.models import VOIngredient, VODish
from meal_planning.catalogue.domain.enums import IngredientTag, DishTag


class IngredientRepository(Protocol):
    """Repository protocol for ingredients."""

    def add(self, ingredient: VOIngredient) -> Result[VOIngredient, DuplicateError]:
        """Add a new ingredient to the bank."""
        ...

    def get(self, uid: str) -> Result[VOIngredient, NotFoundError]:
        """Get ingredient by uid."""
        ...

    def get_by_name(self, name: str) -> Result[VOIngredient, NotFoundError]:
        """Get ingredient by name (case-insensitive)."""
        ...

    def list_all(self) -> Sequence[VOIngredient]:
        """List all ingredients."""
        ...

    def find_by_tag(self, tag: IngredientTag) -> Sequence[VOIngredient]:
        """Find all ingredients with a specific tag."""
        ...

    def update(self, ingredient: VOIngredient) -> Result[VOIngredient, NotFoundError]:
        """Update an existing ingredient."""
        ...

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete ingredient by uid."""
        ...


class DishRepository(Protocol):
    """Repository protocol for dishes."""

    def add(self, dish: VODish) -> Result[VODish, DuplicateError]:
        """Add a new dish to the bank."""
        ...

    def get(self, uid: str) -> Result[VODish, NotFoundError]:
        """Get dish by uid."""
        ...

    def get_by_name(self, name: str) -> Result[VODish, NotFoundError]:
        """Get dish by name (case-insensitive)."""
        ...

    def list_all(self) -> Sequence[VODish]:
        """List all dishes."""
        ...

    def find_by_tag(self, tag: DishTag) -> Sequence[VODish]:
        """Find all dishes with a specific tag."""
        ...

    def find_by_ingredient(self, ingredient_uid: str) -> Sequence[VODish]:
        """Find all dishes containing a specific ingredient."""
        ...

    def update(self, dish: VODish) -> Result[VODish, NotFoundError]:
        """Update an existing dish."""
        ...

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete dish by uid."""
        ...
