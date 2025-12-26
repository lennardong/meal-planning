"""Planning domain models.

Immutable Pydantic models for meal planning.
MonthlyPlan is the aggregate root containing WeekPlan value objects.
"""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict

from .enums import Day


def _plan_uid() -> str:
    """Generate unique plan identifier."""
    return f"PLAN-{uuid4().hex[:8]}"


class WeekPlan(BaseModel):
    """Value Object: schedule for one week.

    Contains dish assignments for weekday dinners and weekend meals.
    Dishes are referenced by UID (or None if unscheduled).
    """

    model_config = ConfigDict(frozen=True)

    weekday_dinners: dict[Day, str | None] = Field(
        default_factory=lambda: {
            Day.MON: None,
            Day.TUE: None,
            Day.WED: None,
            Day.THU: None,
            Day.FRI: None,
        }
    )
    weekend_meals: dict[Day, str | None] = Field(
        default_factory=lambda: {
            Day.SAT: None,
            Day.SUN: None,
        }
    )

    def with_dish(self, day: Day, dish_uid: str | None) -> WeekPlan:
        """Return new WeekPlan with dish scheduled for given day.

        Args:
            day: Day to schedule.
            dish_uid: Dish UID or None to clear.

        Returns:
            New WeekPlan with updated schedule.
        """
        if day in Day.weekend():
            return self.model_copy(
                update={"weekend_meals": {**self.weekend_meals, day: dish_uid}}
            )
        return self.model_copy(
            update={"weekday_dinners": {**self.weekday_dinners, day: dish_uid}}
        )

    def get_dish(self, day: Day) -> str | None:
        """Get dish UID for a specific day."""
        if day in Day.weekend():
            return self.weekend_meals.get(day)
        return self.weekday_dinners.get(day)

    def all_dish_uids(self) -> tuple[str | None, ...]:
        """Get all dish UIDs scheduled this week (including None)."""
        return tuple(self.weekday_dinners.values()) + tuple(
            self.weekend_meals.values()
        )

    def scheduled_dish_uids(self) -> tuple[str, ...]:
        """Get only scheduled dish UIDs (excluding None)."""
        return tuple(uid for uid in self.all_dish_uids() if uid is not None)


class MonthlyPlan(BaseModel):
    """Aggregate Root: monthly meal plan with 4 weeks.

    Represents a complete month of meal planning.
    Contains exactly 4 WeekPlan value objects (W1-W4).
    """

    model_config = ConfigDict(frozen=True)

    uid: str = Field(default_factory=_plan_uid)
    month: str  # Format: "2025-01"
    weeks: tuple[WeekPlan, WeekPlan, WeekPlan, WeekPlan] = Field(
        default_factory=lambda: (WeekPlan(), WeekPlan(), WeekPlan(), WeekPlan())
    )

    def with_week(self, week_num: int, week: WeekPlan) -> MonthlyPlan:
        """Return new MonthlyPlan with updated week.

        Args:
            week_num: Week number (1-4).
            week: New WeekPlan.

        Returns:
            New MonthlyPlan with updated week.

        Raises:
            ValueError: If week_num not in 1-4.
        """
        if not 1 <= week_num <= 4:
            raise ValueError(f"Week number must be 1-4, got {week_num}")

        weeks_list = list(self.weeks)
        weeks_list[week_num - 1] = week
        return self.model_copy(update={"weeks": tuple(weeks_list)})

    def schedule_dish(
        self, week_num: int, day: Day, dish_uid: str | None
    ) -> MonthlyPlan:
        """Convenience method to schedule a dish in one call.

        Args:
            week_num: Week number (1-4).
            day: Day of week.
            dish_uid: Dish UID or None to clear.

        Returns:
            New MonthlyPlan with dish scheduled.
        """
        week = self.weeks[week_num - 1]
        updated_week = week.with_dish(day, dish_uid)
        return self.with_week(week_num, updated_week)

    def all_scheduled_dish_uids(self) -> tuple[str, ...]:
        """Get all scheduled dish UIDs across all weeks."""
        result: list[str] = []
        for week in self.weeks:
            result.extend(week.scheduled_dish_uids())
        return tuple(result)

    @classmethod
    def for_month(cls, month: str) -> MonthlyPlan:
        """Create a new plan for a specific month.

        Args:
            month: Month in format "YYYY-MM" (e.g., "2025-01").

        Returns:
            New MonthlyPlan with uid based on month.
        """
        return cls(uid=f"PLAN-{month}", month=month)
