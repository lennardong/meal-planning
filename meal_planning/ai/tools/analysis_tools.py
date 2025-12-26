"""Analysis tools for AI agent.

Wrappers around planning services for AI agent use.
"""

from __future__ import annotations

from meal_planning.catalogue.repositories.protocols import IngredientRepository, DishRepository
from meal_planning.planning.domain.models import MonthlyPlan
from meal_planning.planning.services.shopping import (
    ShoppingList,
    generate_shopping_list,
    generate_monthly_shopping_list,
)
from meal_planning.planning.services.analysis import (
    VarietyReport,
    assess_variety,
    suggest_improvements,
)


def get_shopping_list(
    plan: MonthlyPlan,
    week_num: int,
    dish_repo: DishRepository,
    ingredient_repo: IngredientRepository,
) -> ShoppingList:
    """Get shopping list for a specific week.

    Args:
        plan: Monthly plan.
        week_num: Week number (1-4).
        dish_repo: Dish repository.
        ingredient_repo: Ingredient repository.

    Returns:
        Shopping list with bulk and weekly items.
    """
    return generate_shopping_list(plan, week_num, dish_repo, ingredient_repo)


def get_monthly_shopping_list(
    plan: MonthlyPlan,
    dish_repo: DishRepository,
    ingredient_repo: IngredientRepository,
) -> ShoppingList:
    """Get shopping list for entire month.

    Args:
        plan: Monthly plan.
        dish_repo: Dish repository.
        ingredient_repo: Ingredient repository.

    Returns:
        Shopping list with all ingredients for the month.
    """
    return generate_monthly_shopping_list(plan, dish_repo, ingredient_repo)


def get_variety_report(
    plan: MonthlyPlan,
    dish_repo: DishRepository,
) -> VarietyReport:
    """Analyze variety in a meal plan.

    Args:
        plan: Monthly plan to analyze.
        dish_repo: Dish repository.

    Returns:
        Variety analysis report.
    """
    return assess_variety(plan, dish_repo)


def get_improvement_suggestions(
    plan: MonthlyPlan,
    dish_repo: DishRepository,
) -> list[str]:
    """Get suggestions for improving meal plan variety.

    Args:
        plan: Monthly plan to analyze.
        dish_repo: Dish repository.

    Returns:
        List of improvement suggestions.
    """
    report = assess_variety(plan, dish_repo)
    return suggest_improvements(report, dish_repo)
