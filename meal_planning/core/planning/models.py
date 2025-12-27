"""Planning domain models.

Simplified models for meal planning:
- WeekPlan: Just a list of dish UIDs (no day assignment)
- MealPlan: N weeks of dishes
- Shortlist: User's selection of dishes to plan with
"""

from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel, Field, ConfigDict


def _plan_uid() -> str:
    """Generate unique plan identifier."""
    return f"PLAN-{uuid4().hex[:8]}"


class WeekPlan(BaseModel):
    """A week's worth of dishes - no day assignment.

    Simply a list of dish UIDs scheduled for this week.
    """

    model_config = ConfigDict(frozen=True)

    dishes: tuple[str, ...] = Field(default_factory=tuple)

    def with_dish(self, dish_uid: str) -> WeekPlan:
        """Return new WeekPlan with dish added."""
        if dish_uid in self.dishes:
            return self
        return self.model_copy(update={"dishes": (*self.dishes, dish_uid)})

    def without_dish(self, dish_uid: str) -> WeekPlan:
        """Return new WeekPlan with dish removed."""
        return self.model_copy(
            update={"dishes": tuple(uid for uid in self.dishes if uid != dish_uid)}
        )

    @property
    def dish_count(self) -> int:
        """Number of dishes in this week."""
        return len(self.dishes)


class MealPlan(BaseModel):
    """A meal plan for N weeks.

    Represents a complete meal plan with variable number of weeks.
    Each week contains a list of dish UIDs.
    """

    model_config = ConfigDict(frozen=True)

    uid: str = Field(default_factory=_plan_uid)
    name: str  # e.g., "January 2025", "Q1 Plan"
    weeks: tuple[WeekPlan, ...] = Field(default_factory=tuple)

    @classmethod
    def create(cls, name: str, num_weeks: int) -> MealPlan:
        """Create a new plan with N empty weeks.

        Args:
            name: Plan name (e.g., "January 2025").
            num_weeks: Number of weeks in the plan.

        Returns:
            New MealPlan with empty weeks.
        """
        return cls(
            name=name,
            weeks=tuple(WeekPlan() for _ in range(num_weeks)),
        )

    @property
    def num_weeks(self) -> int:
        """Number of weeks in this plan."""
        return len(self.weeks)

    @property
    def total_dishes(self) -> int:
        """Total number of dish slots across all weeks."""
        return sum(week.dish_count for week in self.weeks)

    def all_dish_uids(self) -> tuple[str, ...]:
        """Get all dish UIDs across all weeks."""
        result: list[str] = []
        for week in self.weeks:
            result.extend(week.dishes)
        return tuple(result)

    def with_week(self, week_num: int, week: WeekPlan) -> MealPlan:
        """Return new MealPlan with updated week.

        Args:
            week_num: Week number (1-indexed).
            week: New WeekPlan.

        Returns:
            New MealPlan with updated week.

        Raises:
            ValueError: If week_num out of range.
        """
        if not 1 <= week_num <= len(self.weeks):
            raise ValueError(f"Week number must be 1-{len(self.weeks)}, got {week_num}")

        weeks_list = list(self.weeks)
        weeks_list[week_num - 1] = week
        return self.model_copy(update={"weeks": tuple(weeks_list)})


class Shortlist(BaseModel):
    """User's selection of dishes to plan with.

    A persistent list of dish UIDs that the user wants to
    include when generating a meal plan.
    """

    model_config = ConfigDict(frozen=True)

    dish_uids: tuple[str, ...] = Field(default_factory=tuple)

    def add(self, dish_uid: str) -> Shortlist:
        """Return new Shortlist with dish added."""
        if dish_uid in self.dish_uids:
            return self
        return self.model_copy(update={"dish_uids": (*self.dish_uids, dish_uid)})

    def remove(self, dish_uid: str) -> Shortlist:
        """Return new Shortlist with dish removed."""
        return self.model_copy(
            update={
                "dish_uids": tuple(uid for uid in self.dish_uids if uid != dish_uid)
            }
        )

    def clear(self) -> Shortlist:
        """Return new empty Shortlist."""
        return self.model_copy(update={"dish_uids": ()})

    def __len__(self) -> int:
        """Number of dishes in shortlist."""
        return len(self.dish_uids)

    def __contains__(self, dish_uid: str) -> bool:
        """Check if dish is in shortlist."""
        return dish_uid in self.dish_uids
