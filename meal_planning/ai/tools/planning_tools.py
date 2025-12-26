"""Planning tools for AI agent.

These functions are exposed to the AI agent for reading and modifying plans.
"""

from __future__ import annotations

from meal_planning.shared.types import Result, Ok, Err, NotFoundError
from meal_planning.planning.domain.models import MonthlyPlan
from meal_planning.planning.domain.enums import Day
from meal_planning.planning.repositories.protocols import PlanRepository


def get_plan(
    repo: PlanRepository,
    month: str,
) -> Result[MonthlyPlan, NotFoundError]:
    """Get plan for a specific month.

    Args:
        repo: Plan repository.
        month: Month in format "YYYY-MM".

    Returns:
        Result with plan or NotFoundError.
    """
    return repo.get_by_month(month)


def get_or_create_plan(
    repo: PlanRepository,
    month: str,
) -> MonthlyPlan:
    """Get existing plan or create new one.

    Args:
        repo: Plan repository (must be JsonPlanRepository with get_or_create).
        month: Month in format "YYYY-MM".

    Returns:
        Existing or new plan for the month.
    """
    # Type narrowing for JsonPlanRepository which has get_or_create
    if hasattr(repo, "get_or_create"):
        return repo.get_or_create(month)

    # Fallback for generic repository
    result = repo.get_by_month(month)
    if result.is_ok():
        return result.unwrap()

    plan = MonthlyPlan.for_month(month)
    repo.add(plan)
    return plan


def schedule_dish(
    repo: PlanRepository,
    month: str,
    week_num: int,
    day: Day,
    dish_uid: str | None,
) -> Result[MonthlyPlan, NotFoundError]:
    """Schedule a dish for a specific day.

    Args:
        repo: Plan repository.
        month: Month in format "YYYY-MM".
        week_num: Week number (1-4).
        day: Day of week.
        dish_uid: Dish UID to schedule, or None to clear.

    Returns:
        Result with updated plan or NotFoundError.
    """
    plan_result = repo.get_by_month(month)
    if plan_result.is_err():
        return plan_result

    plan = plan_result.unwrap()
    updated_plan = plan.schedule_dish(week_num, day, dish_uid)

    return repo.update(updated_plan)


def get_week_schedule(
    repo: PlanRepository,
    month: str,
    week_num: int,
) -> dict[str, str | None] | None:
    """Get schedule for a specific week as a dict.

    Args:
        repo: Plan repository.
        month: Month in format "YYYY-MM".
        week_num: Week number (1-4).

    Returns:
        Dict mapping day names to dish UIDs, or None if plan not found.
    """
    plan_result = repo.get_by_month(month)
    if plan_result.is_err():
        return None

    plan = plan_result.unwrap()
    if not 1 <= week_num <= 4:
        return None

    week = plan.weeks[week_num - 1]

    schedule = {}
    for day in Day.weekdays():
        schedule[day.value] = week.weekday_dinners.get(day)
    for day in Day.weekend():
        schedule[day.value] = week.weekend_meals.get(day)

    return schedule
