"""Planning service - manages meal plans.

This service handles:
- Loading/saving monthly plans from blob storage
- JSON serialization/deserialization
- User-scoped key construction
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from meal_planning.core.planning.models import MonthlyPlan
from meal_planning.core.planning.enums import Day
from meal_planning.core.shared.types import Result, Ok, Err, NotFoundError, DuplicateError

if TYPE_CHECKING:
    from meal_planning.services.ports.blobstore import BlobStore


class PlanningService:
    """Manages meal plans with JSON persistence."""

    def __init__(self, store: BlobStore, user_id: str = "default"):
        """Initialize the planning service.

        Args:
            store: Blob store for persistence.
            user_id: User identifier for data scoping.
        """
        self._store = store
        self._user_id = user_id
        self._plans: dict[str, MonthlyPlan] = {}
        self._loaded = False

    def _key(self, filename: str) -> str:
        """Construct blob key with user scoping."""
        return f"{self._user_id}/{filename}"

    def _ensure_loaded(self) -> None:
        """Lazy load data from store."""
        if self._loaded:
            return

        plan_bytes = self._store.load_blob(self._key("plans.json"))
        if plan_bytes:
            plan_data = json.loads(plan_bytes.decode("utf-8"))
            self._plans = {
                uid: MonthlyPlan.model_validate(data)
                for uid, data in plan_data.items()
            }

        self._loaded = True

    def save(self) -> None:
        """Persist all data to blob store."""
        plan_data = {uid: plan.model_dump() for uid, plan in self._plans.items()}
        self._store.save_blob(
            self._key("plans.json"),
            json.dumps(plan_data, indent=2).encode("utf-8"),
        )

    def create_plan(self, month: str) -> Result[MonthlyPlan, DuplicateError]:
        """Create a new monthly plan.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            Ok(plan) if created, Err if already exists.
        """
        self._ensure_loaded()
        plan = MonthlyPlan.for_month(month)
        if plan.uid in self._plans:
            return Err(DuplicateError("Plan", plan.uid))
        self._plans[plan.uid] = plan
        return Ok(plan)

    def get_plan(self, uid: str) -> Result[MonthlyPlan, NotFoundError]:
        """Get a plan by UID.

        Args:
            uid: Plan UID (e.g., "PLAN-2025-01").

        Returns:
            Ok(plan) if found, Err if not found.
        """
        self._ensure_loaded()
        plan = self._plans.get(uid)
        if plan is None:
            return Err(NotFoundError("Plan", uid))
        return Ok(plan)

    def get_plan_for_month(self, month: str) -> Result[MonthlyPlan, NotFoundError]:
        """Get a plan by month.

        Args:
            month: Month in format "YYYY-MM".

        Returns:
            Ok(plan) if found, Err if not found.
        """
        uid = f"PLAN-{month}"
        return self.get_plan(uid)

    def list_plans(self) -> list[MonthlyPlan]:
        """Get all plans."""
        self._ensure_loaded()
        return list(self._plans.values())

    def schedule_dish(
        self,
        plan_uid: str,
        week_num: int,
        day: Day,
        dish_uid: str | None,
    ) -> Result[MonthlyPlan, NotFoundError]:
        """Schedule a dish in a plan.

        Args:
            plan_uid: Plan UID.
            week_num: Week number (1-4).
            day: Day of week.
            dish_uid: Dish UID or None to clear.

        Returns:
            Ok(updated_plan) if scheduled, Err if plan not found.
        """
        self._ensure_loaded()
        plan = self._plans.get(plan_uid)
        if plan is None:
            return Err(NotFoundError("Plan", plan_uid))

        updated_plan = plan.schedule_dish(week_num, day, dish_uid)
        self._plans[plan_uid] = updated_plan
        return Ok(updated_plan)

    def delete_plan(self, uid: str) -> Result[None, NotFoundError]:
        """Delete a plan.

        Args:
            uid: Plan UID.

        Returns:
            Ok(None) if deleted, Err if not found.
        """
        self._ensure_loaded()
        if uid not in self._plans:
            return Err(NotFoundError("Plan", uid))
        del self._plans[uid]
        return Ok(None)
