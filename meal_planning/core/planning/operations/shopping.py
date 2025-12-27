"""Shopping list generation operations.

Pure functions for generating shopping lists from meal plans.
These functions take domain objects as input and return domain objects.
No I/O operations - repositories are passed as dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from meal_planning.core.catalogue.models import VOIngredient, VODish
from meal_planning.core.catalogue.enums import PurchaseType
from meal_planning.core.planning.models import MonthlyPlan


@dataclass(frozen=True)
class ShoppingList:
    """Shopping list separated by purchase type."""

    bulk: tuple[VOIngredient, ...]
    weekly: tuple[VOIngredient, ...]

    def all_ingredients(self) -> tuple[VOIngredient, ...]:
        """Get all ingredients combined."""
        return self.bulk + self.weekly

    def bulk_names(self) -> tuple[str, ...]:
        """Get names of bulk items."""
        return tuple(ing.name for ing in self.bulk)

    def weekly_names(self) -> tuple[str, ...]:
        """Get names of weekly items."""
        return tuple(ing.name for ing in self.weekly)


def generate_shopping_list(
    plan: MonthlyPlan,
    week_num: int,
    dishes: Sequence[VODish],
    ingredients: Sequence[VOIngredient],
) -> ShoppingList:
    """Generate shopping list for a specific week.

    Pure function that composes data from domain objects.

    Args:
        plan: Monthly plan containing the week.
        week_num: Week number (1-4).
        dishes: All available dishes (for lookup).
        ingredients: All available ingredients (for lookup).

    Returns:
        ShoppingList with bulk and weekly items separated.
    """
    if not 1 <= week_num <= 4:
        raise ValueError(f"Week number must be 1-4, got {week_num}")

    # Build lookup dictionaries
    dish_by_uid = {d.uid: d for d in dishes}
    ingredient_by_uid = {i.uid: i for i in ingredients}

    week = plan.weeks[week_num - 1]
    dish_uids = week.scheduled_dish_uids()

    seen_ingredients: set[str] = set()
    bulk_items: list[VOIngredient] = []
    weekly_items: list[VOIngredient] = []

    for dish_uid in dish_uids:
        dish = dish_by_uid.get(dish_uid)
        if dish is None:
            continue  # Skip missing dishes

        for ing_uid in dish.ingredient_uids:
            if ing_uid in seen_ingredients:
                continue
            seen_ingredients.add(ing_uid)

            ing = ingredient_by_uid.get(ing_uid)
            if ing is None:
                continue  # Skip missing ingredients

            if ing.purchase_type == PurchaseType.BULK:
                bulk_items.append(ing)
            else:
                weekly_items.append(ing)

    return ShoppingList(
        bulk=tuple(sorted(bulk_items, key=lambda x: x.name)),
        weekly=tuple(sorted(weekly_items, key=lambda x: x.name)),
    )


def generate_monthly_shopping_list(
    plan: MonthlyPlan,
    dishes: Sequence[VODish],
    ingredients: Sequence[VOIngredient],
) -> ShoppingList:
    """Generate shopping list for entire month.

    Useful for bulk purchasing at start of month.

    Args:
        plan: Monthly plan.
        dishes: All available dishes (for lookup).
        ingredients: All available ingredients (for lookup).

    Returns:
        ShoppingList with all ingredients for the month.
    """
    # Build lookup dictionaries
    dish_by_uid = {d.uid: d for d in dishes}
    ingredient_by_uid = {i.uid: i for i in ingredients}

    all_dish_uids = plan.all_scheduled_dish_uids()

    seen_ingredients: set[str] = set()
    bulk_items: list[VOIngredient] = []
    weekly_items: list[VOIngredient] = []

    for dish_uid in all_dish_uids:
        dish = dish_by_uid.get(dish_uid)
        if dish is None:
            continue

        for ing_uid in dish.ingredient_uids:
            if ing_uid in seen_ingredients:
                continue
            seen_ingredients.add(ing_uid)

            ing = ingredient_by_uid.get(ing_uid)
            if ing is None:
                continue

            if ing.purchase_type == PurchaseType.BULK:
                bulk_items.append(ing)
            else:
                weekly_items.append(ing)

    return ShoppingList(
        bulk=tuple(sorted(bulk_items, key=lambda x: x.name)),
        weekly=tuple(sorted(weekly_items, key=lambda x: x.name)),
    )
