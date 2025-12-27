"""AI Assistant service - orchestrates AI-driven meal planning.

This service coordinates AI client interactions with other services
to provide intelligent meal planning suggestions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from meal_planning.core.planning.enums import Day

if TYPE_CHECKING:
    from meal_planning.services.ports.ai_client import AIClientPort
    from meal_planning.services.catalogue import CatalogueService
    from meal_planning.services.planning import PlanningService
    from meal_planning.services.context import ContextService


# Prompt templates
SYSTEM_PROMPT = """You are a helpful meal planning assistant. You help users plan their weekly and monthly meals.

## Your Capabilities
- View and manage a catalogue of ingredients and dishes
- Create and modify monthly meal plans (4 weeks per month)
- Generate shopping lists separated by bulk vs weekly purchase items
- Analyze meal variety and suggest improvements

## User Context
{user_context}

## Available Dishes
{available_dishes}

## Guidelines
1. Always consider the user's dietary preferences and constraints
2. Aim for variety - mix Eastern and Western dishes
3. Don't schedule the same dish more than 2-3 times per month
4. Consider ingredient reuse for efficiency
5. Balance weekday convenience with weekend cooking enjoyment

When suggesting meals:
- Explain your reasoning
- Consider the user's preferences
- Balance variety with practicality
"""


class AIAssistantService:
    """AI-powered meal planning assistant."""

    def __init__(
        self,
        catalogue: CatalogueService,
        planning: PlanningService,
        context: ContextService,
        ai_client: AIClientPort | None = None,
    ):
        """Initialize the AI assistant.

        Args:
            catalogue: Catalogue service for dish data.
            planning: Planning service for plan data.
            context: Context service for user preferences.
            ai_client: Optional AI client for suggestions.
        """
        self._catalogue = catalogue
        self._planning = planning
        self._context = context
        self._ai_client = ai_client

    @property
    def has_ai(self) -> bool:
        """Check if AI client is available."""
        return self._ai_client is not None

    def _format_dishes_for_prompt(self) -> str:
        """Format available dishes for AI prompt."""
        dishes = self._catalogue.list_dishes()
        if not dishes:
            return "No dishes available"

        lines = []
        for dish in dishes:
            tags = ", ".join(str(tag) for tag in dish.tags)
            line = f"- {dish.name}"
            if tags:
                line += f" ({tags})"
            lines.append(line)

        return "\n".join(lines)

    def _get_system_prompt(self) -> str:
        """Build system prompt with current context."""
        user_context = self._context.get_all_context_text()
        if not user_context:
            user_context = "No specific preferences set."

        return SYSTEM_PROMPT.format(
            user_context=user_context,
            available_dishes=self._format_dishes_for_prompt(),
        )

    def get_plan_summary(self, month: str) -> str | None:
        """Get a text summary of a month's plan.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            Human-readable summary, or None if plan not found.
        """
        plan_result = self._planning.get_plan_for_month(month)
        if plan_result.is_err():
            return None

        plan = plan_result.unwrap()
        lines = [f"Meal Plan for {month}", "=" * 40]

        for i, week in enumerate(plan.weeks, 1):
            lines.append(f"\nWeek {i}:")
            lines.append("-" * 20)

            # Weekday dinners
            for day in Day.weekdays():
                dish_uid = week.weekday_dinners.get(day)
                dish_name = self._get_dish_name(dish_uid)
                lines.append(f"  {day.value}: {dish_name}")

            # Weekend meals
            for day in Day.weekend():
                dish_uid = week.weekend_meals.get(day)
                dish_name = self._get_dish_name(dish_uid)
                lines.append(f"  {day.value}: {dish_name}")

        return "\n".join(lines)

    def _get_dish_name(self, dish_uid: str | None) -> str:
        """Get dish name from UID."""
        if dish_uid is None:
            return "(not scheduled)"

        dish_result = self._catalogue.get_dish(dish_uid)
        if dish_result.is_err():
            return f"[Unknown: {dish_uid}]"
        return dish_result.unwrap().name

    def suggest_plan(self, month: str) -> str | None:
        """Use AI to suggest a monthly plan.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            AI suggestion text, or None if no AI client.
        """
        if self._ai_client is None:
            return None

        system_prompt = self._get_system_prompt()
        user_message = f"Please create a meal plan for {month}."

        response = self._ai_client.complete(
            prompt=user_message,
            system=system_prompt,
            max_tokens=2048,
        )

        return response.content

    def chat(self, message: str) -> str | None:
        """Have a conversation about meal planning.

        Args:
            message: User message.

        Returns:
            AI response, or None if no AI client.
        """
        if self._ai_client is None:
            return None

        system_prompt = self._get_system_prompt()

        response = self._ai_client.complete(
            prompt=message,
            system=system_prompt,
            max_tokens=1024,
        )

        return response.content
