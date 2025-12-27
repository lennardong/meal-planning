"""Planning operations - pure domain functions."""

from meal_planning.core.planning.operations.shopping import (
    ShoppingList,
    generate_shopping_list,
    generate_monthly_shopping_list,
)
from meal_planning.core.planning.operations.analysis import (
    VarietyReport,
    calculate_variety_score,
    assess_variety,
    suggest_improvements,
)

__all__ = [
    "ShoppingList",
    "generate_shopping_list",
    "generate_monthly_shopping_list",
    "VarietyReport",
    "calculate_variety_score",
    "assess_variety",
    "suggest_improvements",
]
