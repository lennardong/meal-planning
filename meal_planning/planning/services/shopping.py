"""Shopping list generation service.

Pure functions for generating shopping lists from meal plans.
"""

from __future__ import annotations

from dataclasses import dataclass

from meal_planning.catalogue.domain.models import VOIngredient
from meal_planning.catalogue.domain.enums import PurchaseType
from meal_planning.catalogue.repositories.protocols import IngredientRepository, DishRepository
from meal_planning.planning.domain.models import MonthlyPlan


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
    dish_repo: DishRepository,
    ingredient_repo: IngredientRepository,
) -> ShoppingList:
    """Generate shopping list for a specific week.

    Pure function that composes data from multiple aggregates.

    Args:
        plan: Monthly plan containing the week.
        week_num: Week number (1-4).
        dish_repo: Repository to look up dishes.
        ingredient_repo: Repository to look up ingredients.

    Returns:
        ShoppingList with bulk and weekly items separated.
    """
    if not 1 <= week_num <= 4:
        raise ValueError(f"Week number must be 1-4, got {week_num}")

    week = plan.weeks[week_num - 1]
    dish_uids = week.scheduled_dish_uids()

    seen_ingredients: set[str] = set()
    bulk_items: list[VOIngredient] = []
    weekly_items: list[VOIngredient] = []

    for dish_uid in dish_uids:
        dish_result = dish_repo.get(dish_uid)
        if dish_result.is_err():
            continue  # Skip missing dishes

        dish = dish_result.unwrap()

        for ing_uid in dish.ingredient_uids:
            if ing_uid in seen_ingredients:
                continue
            seen_ingredients.add(ing_uid)

            ing_result = ingredient_repo.get(ing_uid)
            if ing_result.is_err():
                continue  # Skip missing ingredients

            ing = ing_result.unwrap()
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
    dish_repo: DishRepository,
    ingredient_repo: IngredientRepository,
) -> ShoppingList:
    """Generate shopping list for entire month.

    Useful for bulk purchasing at start of month.

    Args:
        plan: Monthly plan.
        dish_repo: Repository to look up dishes.
        ingredient_repo: Repository to look up ingredients.

    Returns:
        ShoppingList with all ingredients for the month.
    """
    all_dish_uids = plan.all_scheduled_dish_uids()

    seen_ingredients: set[str] = set()
    bulk_items: list[VOIngredient] = []
    weekly_items: list[VOIngredient] = []

    for dish_uid in all_dish_uids:
        dish_result = dish_repo.get(dish_uid)
        if dish_result.is_err():
            continue

        dish = dish_result.unwrap()

        for ing_uid in dish.ingredient_uids:
            if ing_uid in seen_ingredients:
                continue
            seen_ingredients.add(ing_uid)

            ing_result = ingredient_repo.get(ing_uid)
            if ing_result.is_err():
                continue

            ing = ing_result.unwrap()
            if ing.purchase_type == PurchaseType.BULK:
                bulk_items.append(ing)
            else:
                weekly_items.append(ing)

    return ShoppingList(
        bulk=tuple(sorted(bulk_items, key=lambda x: x.name)),
        weekly=tuple(sorted(weekly_items, key=lambda x: x.name)),
    )
