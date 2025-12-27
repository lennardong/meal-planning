"""Planning service - manages shortlist and meal plans.

This service handles:
- Shortlist management (add/remove dishes for planning)
- Meal plan creation with automatic dish distribution
- Auto-save after all mutations
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Sequence

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.planning.models import MealPlan, WeekPlan, Shortlist
from meal_planning.core.planning.operations.distribution import (
    DistributionResult,
    distribute_dishes,
)
from meal_planning.core.shared.types import Result, Ok, Err, NotFoundError

if TYPE_CHECKING:
    from meal_planning.services.ports.blobstore import BlobStore


class PlanningService:
    """Manages shortlist and meal plans with auto-save."""

    def __init__(self, store: "BlobStore", user_id: str = "default"):
        """Initialize the planning service.

        Args:
            store: Blob store for persistence.
            user_id: User identifier for data scoping.
        """
        self._store = store
        self._user_id = user_id
        self._shortlist: Shortlist = Shortlist()
        self._plans: dict[str, MealPlan] = {}
        self._loaded = False

    def _key(self, filename: str) -> str:
        """Construct blob key with user scoping."""
        return f"{self._user_id}/{filename}"

    def _ensure_loaded(self) -> None:
        """Lazy load data from store."""
        if self._loaded:
            return

        # Load shortlist
        shortlist_bytes = self._store.load_blob(self._key("shortlist.json"))
        if shortlist_bytes:
            shortlist_data = json.loads(shortlist_bytes.decode("utf-8"))
            self._shortlist = Shortlist.model_validate(shortlist_data)

        # Load plans
        plan_bytes = self._store.load_blob(self._key("plans.json"))
        if plan_bytes:
            plan_data = json.loads(plan_bytes.decode("utf-8"))
            self._plans = {
                uid: MealPlan.model_validate(data)
                for uid, data in plan_data.items()
            }

        self._loaded = True

    def _save(self) -> None:
        """Auto-save shortlist and plans."""
        # Save shortlist
        self._store.save_blob(
            self._key("shortlist.json"),
            json.dumps(self._shortlist.model_dump(), indent=2).encode("utf-8"),
        )
        # Save plans
        plan_data = {uid: plan.model_dump() for uid, plan in self._plans.items()}
        self._store.save_blob(
            self._key("plans.json"),
            json.dumps(plan_data, indent=2).encode("utf-8"),
        )

    # === Shortlist Operations (auto-save) ===

    def add_to_shortlist(self, dish_uid: str) -> Shortlist:
        """Add dish to shortlist.

        Args:
            dish_uid: Dish UID to add.

        Returns:
            Updated shortlist.
        """
        self._ensure_loaded()
        self._shortlist = self._shortlist.add(dish_uid)
        self._save()
        return self._shortlist

    def remove_from_shortlist(self, dish_uid: str) -> Shortlist:
        """Remove dish from shortlist.

        Args:
            dish_uid: Dish UID to remove.

        Returns:
            Updated shortlist.
        """
        self._ensure_loaded()
        self._shortlist = self._shortlist.remove(dish_uid)
        self._save()
        return self._shortlist

    def clear_shortlist(self) -> Shortlist:
        """Clear all dishes from shortlist.

        Returns:
            Empty shortlist.
        """
        self._ensure_loaded()
        self._shortlist = self._shortlist.clear()
        self._save()
        return self._shortlist

    def get_shortlist(self) -> Shortlist:
        """Get current shortlist.

        Returns:
            Current shortlist.
        """
        self._ensure_loaded()
        return self._shortlist

    # === Plan Operations (auto-save) ===

    def create_plan(
        self,
        name: str,
        dishes: Sequence[Dish],
        weeks: int = 4,
        dishes_per_week: int = 4,
        eastern_per_week: int = 2,
        western_per_week: int = 2,
    ) -> tuple[MealPlan, DistributionResult]:
        """Create a meal plan by distributing dishes across weeks.

        Distributes dishes to maximize:
        - Food category diversity (greens, grains, fermented, etc.)
        - Cuisine novelty (Korean, Thai, Italian, etc.)
        - Regional balance (Eastern/Western constraint)

        Args:
            name: Plan name (e.g., "January 2025").
            dishes: Dishes to distribute (from shortlist).
            weeks: Number of weeks (default 4).
            dishes_per_week: Dishes per week (default 4).
            eastern_per_week: Eastern dishes per week (default 2).
            western_per_week: Western dishes per week (default 2).

        Returns:
            Tuple of (MealPlan, DistributionResult).
        """
        self._ensure_loaded()

        # Distribute dishes using pure domain function
        result = distribute_dishes(
            dishes,
            weeks=weeks,
            per_week=dishes_per_week,
            eastern_per_week=eastern_per_week,
            western_per_week=western_per_week,
        )

        # Build plan from distribution result
        week_plans = [WeekPlan(dishes=week_uids) for week_uids in result.weeks]
        plan = MealPlan(name=name, weeks=tuple(week_plans))

        # Store and save
        self._plans[plan.uid] = plan
        self._save()

        return plan, result

    def get_plan(self, uid: str) -> Result[MealPlan, NotFoundError]:
        """Get a plan by UID.

        Args:
            uid: Plan UID.

        Returns:
            Ok(plan) if found, Err if not found.
        """
        self._ensure_loaded()
        plan = self._plans.get(uid)
        if plan is None:
            return Err(NotFoundError("Plan", uid))
        return Ok(plan)

    def get_plan_by_name(self, name: str) -> Result[MealPlan, NotFoundError]:
        """Get a plan by name (case-insensitive).

        Args:
            name: Plan name.

        Returns:
            Ok(plan) if found, Err if not found.
        """
        self._ensure_loaded()
        name_lower = name.lower()
        for plan in self._plans.values():
            if plan.name.lower() == name_lower:
                return Ok(plan)
        return Err(NotFoundError("Plan", name))

    def list_plans(self) -> list[MealPlan]:
        """Get all plans.

        Returns:
            List of all plans.
        """
        self._ensure_loaded()
        return list(self._plans.values())

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
        self._save()
        return Ok(None)
