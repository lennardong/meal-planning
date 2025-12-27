"""Shopping service - generates shopping lists.

This service orchestrates the pure shopping operations
with data from catalogue and planning services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from meal_planning.core.planning.operations.shopping import (
    ShoppingList,
    generate_shopping_list,
    generate_monthly_shopping_list,
)

if TYPE_CHECKING:
    from meal_planning.services.catalogue import CatalogueService
    from meal_planning.services.planning import PlanningService


class ShoppingService:
    """Generates shopping lists from plans."""

    def __init__(
        self,
        catalogue: CatalogueService,
        planning: PlanningService,
    ):
        """Initialize the shopping service.

        Args:
            catalogue: Catalogue service for ingredient/dish data.
            planning: Planning service for plan data.
        """
        self._catalogue = catalogue
        self._planning = planning

    def get_weekly_list(self, month: str, week_num: int) -> ShoppingList | None:
        """Generate shopping list for a specific week.

        Args:
            month: Month in format "YYYY-MM".
            week_num: Week number (1-4).

        Returns:
            ShoppingList if plan exists, None otherwise.
        """
        plan_result = self._planning.get_plan_for_month(month)
        if plan_result.is_err():
            return None

        plan = plan_result.unwrap()
        dishes = self._catalogue.list_dishes()
        ingredients = self._catalogue.list_ingredients()

        return generate_shopping_list(plan, week_num, dishes, ingredients)

    def get_monthly_list(self, month: str) -> ShoppingList | None:
        """Generate shopping list for entire month.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            ShoppingList if plan exists, None otherwise.
        """
        plan_result = self._planning.get_plan_for_month(month)
        if plan_result.is_err():
            return None

        plan = plan_result.unwrap()
        dishes = self._catalogue.list_dishes()
        ingredients = self._catalogue.list_ingredients()

        return generate_monthly_shopping_list(plan, dishes, ingredients)
