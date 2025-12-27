"""Catalogue domain models.

Dish is an entity (has UID for planning references).
Categories are used for dietary diversity tracking.
"""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict, field_validator

from meal_planning.core.catalogue.enums import Category, Cuisine, Region, CUISINE_REGION


def _dish_uid() -> str:
    """Generate unique dish identifier."""
    return f"DISH-{uuid4().hex[:8]}"


class Dish(BaseModel):
    """A dish with food categories and cuisine for diversity tracking.

    Represents a dish that can be scheduled in meal plans.
    Categories are used to ensure dietary variety.
    Cuisine determines the regional classification for balance constraints.
    """

    model_config = ConfigDict(frozen=True)

    uid: str = Field(default_factory=_dish_uid)
    name: str
    categories: tuple[Category, ...] = Field(default_factory=tuple)
    cuisine: Cuisine  # Required: determines region for balance constraint
    tags: tuple[str, ...] = Field(default_factory=tuple)  # Open for custom tags
    recipe_reference: str = ""  # Link to recipe or ingredient notes

    @property
    def region(self) -> Region:
        """Derive region from cuisine for balance constraint."""
        return CUISINE_REGION[self.cuisine]

    @field_validator('name', mode='before')
    @classmethod
    def normalize_name(cls, v: str) -> str:
        """Normalize dish name: strip whitespace, title case."""
        return v.strip().title()

    @field_validator('tags', mode='before')
    @classmethod
    def normalize_tags(cls, v: list | tuple) -> tuple[str, ...]:
        """Normalize tags."""
        if v is None:
            return ()
        return tuple(str(t).strip().title() for t in v)

    @field_validator('categories', mode='before')
    @classmethod
    def normalize_categories(cls, v: list | tuple) -> tuple[Category, ...]:
        """Validate and normalize categories."""
        if v is None:
            return ()
        return tuple(Category(c) for c in v)

    def with_category(self, category: Category) -> Dish:
        """Return new dish with added category."""
        if category in self.categories:
            return self
        return self.model_copy(
            update={"categories": (*self.categories, category)}
        )

    def without_category(self, category: Category) -> Dish:
        """Return new dish with category removed."""
        return self.model_copy(
            update={
                "categories": tuple(
                    cat for cat in self.categories if cat != category
                )
            }
        )

    def with_tags(self, tags: tuple[str, ...]) -> Dish:
        """Return new dish with updated tags."""
        return self.model_copy(update={"tags": tags})

    def with_recipe_reference(self, reference: str) -> Dish:
        """Return new dish with updated recipe reference."""
        return self.model_copy(update={"recipe_reference": reference})

    def with_cuisine(self, cuisine: Cuisine) -> Dish:
        """Return new dish with updated cuisine."""
        return self.model_copy(update={"cuisine": cuisine})
