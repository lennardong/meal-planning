"""Catalogue tools for AI agent.

These functions are exposed to the AI agent for reading catalogue data.
"""

from __future__ import annotations

from typing import Sequence

from meal_planning.catalogue.domain.models import VOIngredient, VODish
from meal_planning.catalogue.domain.enums import IngredientTag, DishTag
from meal_planning.catalogue.repositories.protocols import IngredientRepository, DishRepository


def list_ingredients(
    repo: IngredientRepository,
    tag: IngredientTag | None = None,
) -> Sequence[VOIngredient]:
    """List ingredients, optionally filtered by tag.

    Args:
        repo: Ingredient repository.
        tag: Optional tag to filter by.

    Returns:
        Sequence of matching ingredients.
    """
    if tag is not None:
        return repo.find_by_tag(tag)
    return repo.list_all()


def list_dishes(
    repo: DishRepository,
    tag: DishTag | None = None,
) -> Sequence[VODish]:
    """List dishes, optionally filtered by tag.

    Args:
        repo: Dish repository.
        tag: Optional tag to filter by.

    Returns:
        Sequence of matching dishes.
    """
    if tag is not None:
        return repo.find_by_tag(tag)
    return repo.list_all()


def get_dish_details(
    dish_repo: DishRepository,
    ingredient_repo: IngredientRepository,
    dish_uid: str,
) -> dict | None:
    """Get dish with full ingredient details.

    Args:
        dish_repo: Dish repository.
        ingredient_repo: Ingredient repository.
        dish_uid: UID of dish to look up.

    Returns:
        Dict with dish info and ingredients, or None if not found.
    """
    dish_result = dish_repo.get(dish_uid)
    if dish_result.is_err():
        return None

    dish = dish_result.unwrap()
    ingredients = []
    for ing_uid in dish.ingredient_uids:
        ing_result = ingredient_repo.get(ing_uid)
        if ing_result.is_ok():
            ingredients.append(ing_result.unwrap())

    return {
        "dish": dish,
        "ingredients": ingredients,
    }
