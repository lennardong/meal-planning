"""Planning repository protocols."""

from __future__ import annotations

from typing import Protocol, Sequence

from meal_planning.shared.types import Result, NotFoundError, DuplicateError
from meal_planning.planning.domain.models import MonthlyPlan


class PlanRepository(Protocol):
    """Repository protocol for monthly plans."""

    def add(self, plan: MonthlyPlan) -> Result[MonthlyPlan, DuplicateError]:
        """Add a new monthly plan."""
        ...

    def get(self, uid: str) -> Result[MonthlyPlan, NotFoundError]:
        """Get plan by uid."""
        ...

    def get_by_month(self, month: str) -> Result[MonthlyPlan, NotFoundError]:
        """Get plan by month (e.g., '2025-01')."""
        ...

    def list_all(self) -> Sequence[MonthlyPlan]:
        """List all plans."""
        ...

    def update(self, plan: MonthlyPlan) -> Result[MonthlyPlan, NotFoundError]:
        """Update an existing plan."""
        ...

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete plan by uid."""
        ...
