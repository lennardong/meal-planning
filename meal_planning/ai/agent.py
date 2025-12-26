"""Meal Planning AI Agent.

Orchestrates AI-driven meal planning using Claude API.
The agent is an adapter (not domain) that calls tools to operate on the domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, Sequence

from meal_planning.catalogue.domain.models import VODish
from meal_planning.planning.domain.models import MonthlyPlan
from meal_planning.planning.domain.enums import Day
from meal_planning.planning.services.analysis import VarietyReport
from meal_planning.planning.services.shopping import ShoppingList
from meal_planning.ai.domain.context import VOAIContext
from meal_planning.ai.prompts import format_system_prompt, format_dish_list

if TYPE_CHECKING:
    from meal_planning.app.store import Store


class AIClient(Protocol):
    """Protocol for AI API client (e.g., Claude, OpenAI)."""

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[dict] | None = None,
    ) -> str:
        """Send a chat message and get response."""
        ...


@dataclass
class MealPlanningAgent:
    """AI agent for meal planning tasks.

    Acts as an adapter between the CLI and domain operations.
    Uses AI to make decisions, but executes via domain services.

    This is a simplified agent that doesn't require an actual AI client
    for basic operations. AI-powered suggestions are optional.
    """

    store: "Store"
    contexts: Sequence[VOAIContext]
    client: AIClient | None = None

    @property
    def context_text(self) -> str:
        """Get combined context text for AI prompts."""
        if not self.contexts:
            return "No preferences set."

        parts = []
        for ctx in self.contexts:
            if ctx.category:
                parts.append(f"[{ctx.category}] {ctx.context}")
            else:
                parts.append(ctx.context)
        return "\n".join(parts)

    def list_available_dishes(self) -> Sequence[VODish]:
        """Get all available dishes from catalogue."""
        return self.store.dishes.list_all()

    def get_plan(self, month: str) -> MonthlyPlan:
        """Get or create plan for a month."""
        return self.store.plans.get_or_create(month)

    def schedule_dish(
        self,
        month: str,
        week_num: int,
        day: Day,
        dish_uid: str | None,
    ) -> MonthlyPlan:
        """Schedule a dish for a specific day.

        Args:
            month: Month in format "YYYY-MM".
            week_num: Week number (1-4).
            day: Day of week.
            dish_uid: Dish UID or None to clear.

        Returns:
            Updated plan.
        """
        plan = self.get_plan(month)
        updated_plan = plan.schedule_dish(week_num, day, dish_uid)
        self.store.plans.update(updated_plan)
        return updated_plan

    def generate_shopping_list(self, month: str, week_num: int) -> ShoppingList:
        """Generate shopping list for a week.

        Args:
            month: Month in format "YYYY-MM".
            week_num: Week number (1-4).

        Returns:
            Shopping list with bulk and weekly items.
        """
        from meal_planning.planning.services.shopping import generate_shopping_list

        plan = self.get_plan(month)
        return generate_shopping_list(
            plan, week_num, self.store.dishes, self.store.ingredients
        )

    def assess_variety(self, month: str) -> VarietyReport:
        """Analyze variety in a month's plan.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            Variety analysis report.
        """
        from meal_planning.planning.services.analysis import assess_variety

        plan = self.get_plan(month)
        return assess_variety(plan, self.store.dishes)

    def suggest_monthly_plan(self, month: str) -> MonthlyPlan | None:
        """Use AI to suggest a full monthly plan.

        Requires an AI client to be configured.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            Suggested plan, or None if no AI client.
        """
        if self.client is None:
            return None

        # Get available dishes
        dishes = self.list_available_dishes()
        dishes_info = [{"name": d.name, "tags": list(d.tags)} for d in dishes]

        # Build prompt
        system_prompt = format_system_prompt(
            user_context=self.context_text,
            available_dishes=format_dish_list(dishes_info),
        )

        user_message = f"Please create a meal plan for {month}."

        # Call AI (implementation depends on client)
        # For now, return None - actual AI integration would go here
        # response = self.client.chat(system_prompt, user_message)

        return None

    def get_plan_summary(self, month: str) -> str:
        """Get a text summary of a month's plan.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            Human-readable summary.
        """
        plan = self.get_plan(month)
        lines = [f"Meal Plan for {month}", "=" * 40]

        for i, week in enumerate(plan.weeks, 1):
            lines.append(f"\nWeek {i}:")
            lines.append("-" * 20)

            # Weekday dinners
            for day in Day.weekdays():
                dish_uid = week.weekday_dinners.get(day)
                if dish_uid:
                    dish_result = self.store.dishes.get(dish_uid)
                    dish_name = (
                        dish_result.unwrap().name
                        if dish_result.is_ok()
                        else f"[Unknown: {dish_uid}]"
                    )
                else:
                    dish_name = "(not scheduled)"
                lines.append(f"  {day.value}: {dish_name}")

            # Weekend meals
            for day in Day.weekend():
                dish_uid = week.weekend_meals.get(day)
                if dish_uid:
                    dish_result = self.store.dishes.get(dish_uid)
                    dish_name = (
                        dish_result.unwrap().name
                        if dish_result.is_ok()
                        else f"[Unknown: {dish_uid}]"
                    )
                else:
                    dish_name = "(not scheduled)"
                lines.append(f"  {day.value}: {dish_name}")

        return "\n".join(lines)
