"""Analysis service - analyzes meal plans.

This service orchestrates the pure analysis operations
with data from catalogue and planning services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from meal_planning.core.planning.operations.analysis import (
    VarietyReport,
    assess_variety,
    suggest_improvements,
)

if TYPE_CHECKING:
    from meal_planning.services.catalogue import CatalogueService
    from meal_planning.services.planning import PlanningService


class AnalysisService:
    """Analyzes meal plans for variety and balance."""

    def __init__(
        self,
        catalogue: CatalogueService,
        planning: PlanningService,
    ):
        """Initialize the analysis service.

        Args:
            catalogue: Catalogue service for dish data.
            planning: Planning service for plan data.
        """
        self._catalogue = catalogue
        self._planning = planning

    def get_variety_report(self, month: str) -> VarietyReport | None:
        """Analyze variety in a monthly plan.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            VarietyReport if plan exists, None otherwise.
        """
        plan_result = self._planning.get_plan_for_month(month)
        if plan_result.is_err():
            return None

        plan = plan_result.unwrap()
        dishes = self._catalogue.list_dishes()

        return assess_variety(plan, dishes)

    def get_suggestions(self, month: str) -> list[str] | None:
        """Get improvement suggestions for a plan.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            List of suggestions if plan exists, None otherwise.
        """
        report = self.get_variety_report(month)
        if report is None:
            return None

        dishes = self._catalogue.list_dishes()
        return suggest_improvements(report, dishes)
