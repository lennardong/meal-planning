"""JSON implementations of planning repositories."""

from __future__ import annotations

from typing import Sequence

from meal_planning.planning.domain.models import MonthlyPlan
from meal_planning.shared.persistence.json_store import JsonStore
from meal_planning.shared.types import DuplicateError, Err, NotFoundError, Ok, Result


class JsonPlanRepository:
    """JSON-backed monthly plan repository."""

    def __init__(self, store: JsonStore) -> None:
        self._store = store

    def add(self, plan: MonthlyPlan) -> Result[MonthlyPlan, DuplicateError]:
        """Add a new monthly plan."""
        if plan.uid in self._store.plans:
            return Err(DuplicateError(entity="MonthlyPlan", uid=plan.uid))

        self._store.plans[plan.uid] = plan.model_dump(mode="json")
        return Ok(plan)

    def get(self, uid: str) -> Result[MonthlyPlan, NotFoundError]:
        """Get plan by uid."""
        if uid not in self._store.plans:
            return Err(NotFoundError(entity="MonthlyPlan", uid=uid))

        return Ok(MonthlyPlan.model_validate(self._store.plans[uid]))

    def get_by_month(self, month: str) -> Result[MonthlyPlan, NotFoundError]:
        """Get plan by month (e.g., '2025-01').

        Looks for plan with uid 'PLAN-{month}' or month field matching.
        """
        # First try direct uid lookup
        plan_uid = f"PLAN-{month}"
        if plan_uid in self._store.plans:
            return Ok(MonthlyPlan.model_validate(self._store.plans[plan_uid]))

        # Fallback to searching by month field
        for data in self._store.plans.values():
            if data.get("month") == month:
                return Ok(MonthlyPlan.model_validate(data))

        return Err(NotFoundError(entity="MonthlyPlan", uid=f"month:{month}"))

    def list_all(self) -> Sequence[MonthlyPlan]:
        """List all plans."""
        return [MonthlyPlan.model_validate(data) for data in self._store.plans.values()]

    def update(self, plan: MonthlyPlan) -> Result[MonthlyPlan, NotFoundError]:
        """Update an existing plan."""
        if plan.uid not in self._store.plans:
            return Err(NotFoundError(entity="MonthlyPlan", uid=plan.uid))

        self._store.plans[plan.uid] = plan.model_dump(mode="json")
        return Ok(plan)

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete plan by uid."""
        if uid not in self._store.plans:
            return Err(NotFoundError(entity="MonthlyPlan", uid=uid))

        del self._store.plans[uid]
        return Ok(None)

    def get_or_create(self, month: str) -> MonthlyPlan:
        """Get existing plan for month or create new one.

        Convenience method for ensuring a plan exists.
        """
        result = self.get_by_month(month)
        if result.is_ok():
            return result.unwrap()

        # Create new plan
        plan = MonthlyPlan.for_month(month)
        self.add(plan)
        return plan
