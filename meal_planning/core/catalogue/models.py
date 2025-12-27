"""Catalogue domain models.

Immutable Pydantic models representing ingredients and dishes.
These are aggregate roots in the catalogue bounded context.
"""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

from meal_planning.core.catalogue.enums import PurchaseType, IngredientTag, DishTag


def _ingredient_uid() -> str:
    """Generate unique ingredient identifier."""
    return f"ING-{uuid4().hex[:8]}"


def _dish_uid() -> str:
    """Generate unique dish identifier."""
    return f"DISH-{uuid4().hex[:8]}"


class VOIngredient(BaseModel):
    """Immutable ingredient value object.

    Represents an ingredient that can be used in dishes.
    Tracks purchase type (bulk vs weekly) for shopping list generation.
    """

    model_config = ConfigDict(frozen=True)

    uid: str = Field(default_factory=_ingredient_uid)
    name: str
    tags: tuple[IngredientTag, ...] = Field(default_factory=tuple)
    purchase_type: PurchaseType = PurchaseType.WEEKLY

    def with_tags(self, tags: tuple[IngredientTag, ...]) -> VOIngredient:
        """Return new ingredient with updated tags."""
        return self.model_copy(update={"tags": tags})

    def with_purchase_type(self, purchase_type: PurchaseType) -> VOIngredient:
        """Return new ingredient with updated purchase type."""
        return self.model_copy(update={"purchase_type": purchase_type})


class VODish(BaseModel):
    """Immutable dish value object.

    Represents a dish that can be scheduled in meal plans.
    References ingredients by UID for loose coupling.
    """

    model_config = ConfigDict(frozen=True)

    uid: str = Field(default_factory=_dish_uid)
    name: str
    tags: tuple[DishTag, ...] = Field(default_factory=tuple)
    ingredient_uids: tuple[str, ...] = Field(default_factory=tuple)

    def with_ingredient(self, ingredient_uid: str) -> VODish:
        """Return new dish with added ingredient reference."""
        if ingredient_uid in self.ingredient_uids:
            return self
        return self.model_copy(
            update={"ingredient_uids": (*self.ingredient_uids, ingredient_uid)}
        )

    def without_ingredient(self, ingredient_uid: str) -> VODish:
        """Return new dish with ingredient reference removed."""
        return self.model_copy(
            update={
                "ingredient_uids": tuple(
                    uid for uid in self.ingredient_uids if uid != ingredient_uid
                )
            }
        )

    def with_tags(self, tags: tuple[DishTag, ...]) -> VODish:
        """Return new dish with updated tags."""
        return self.model_copy(update={"tags": tags})
