"""Dish distribution operations.

Pure functions for distributing dishes across weeks to maximize
diversity (food categories) and novelty (cuisines).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.catalogue.enums import Category, Cuisine, Region, CUISINE_REGION


@dataclass(frozen=True)
class DistributionResult:
    """Result of dish distribution algorithm.

    Contains the weekly distribution plus metadata about
    discarded and reused dishes.
    """

    weeks: tuple[tuple[str, ...], ...]  # 4 weeks of dish UIDs
    discarded: tuple[str, ...]  # Dish UIDs that didn't fit
    reused: tuple[str, ...]  # Dish UIDs used more than once


@dataclass
class _WeekState:
    """Mutable state for tracking what's been assigned to a week."""

    categories_used: set[Category] = field(default_factory=set)
    cuisines_used: set[Cuisine] = field(default_factory=set)
    dish_uids: list[str] = field(default_factory=list)

    def add_dish(self, dish: Dish) -> None:
        """Add a dish to this week's state."""
        self.dish_uids.append(dish.uid)
        self.categories_used.update(dish.categories)
        self.cuisines_used.add(dish.cuisine)


def _score_dish(dish: Dish, week_state: _WeekState, recently_used: set[str]) -> float:
    """Score a dish for selection based on diversity and novelty.

    Scoring:
    - +1.0 for each new food category not yet in the week
    - +0.5 for cuisine not yet in the week (novelty bonus)
    - -1.0 penalty for dish used in previous week (spacing)
    """
    score = 0.0

    # Category diversity: more new categories = higher score
    new_cats = set(dish.categories) - week_state.categories_used
    score += len(new_cats)

    # Cuisine novelty: bonus for new cuisine in this week
    if dish.cuisine not in week_state.cuisines_used:
        score += 0.5

    # Spacing penalty: discourage recently used dishes
    if dish.uid in recently_used:
        score -= 1.0

    return score


def _pick_best(
    candidates: list[Dish],
    week_state: _WeekState,
    recently_used: set[str],
) -> Dish | None:
    """Pick the best dish from candidates based on scoring."""
    if not candidates:
        return None
    return max(candidates, key=lambda d: _score_dish(d, week_state, recently_used))


def _separate_by_region(dishes: Sequence[Dish]) -> tuple[list[Dish], list[Dish]]:
    """Separate dishes into Eastern and Western lists."""
    eastern: list[Dish] = []
    western: list[Dish] = []
    for dish in dishes:
        if dish.region == Region.EASTERN:
            eastern.append(dish)
        else:
            western.append(dish)
    return eastern, western


def distribute_dishes(
    dishes: Sequence[Dish],
    weeks: int = 4,
    per_week: int = 4,
    eastern_per_week: int = 2,
    western_per_week: int = 2,
) -> DistributionResult:
    """Distribute dishes across weeks maximizing diversity and novelty.

    Algorithm:
    1. Separate by region (Eastern/Western) using cuisine→region mapping
    2. For each week:
       a. Pick eastern_per_week Eastern dishes: prefer different cuisines, maximize new categories
       b. Pick western_per_week Western dishes: prefer different cuisines, maximize new categories
    3. Handle under/overflow (reuse with spacing or discard)

    Args:
        dishes: Available dishes to distribute
        weeks: Number of weeks (default 4)
        per_week: Dishes per week (default 4)
        eastern_per_week: Required Eastern dishes per week (default 2)
        western_per_week: Required Western dishes per week (default 2)

    Returns:
        DistributionResult with weekly dish UID assignments
    """
    eastern_dishes, western_dishes = _separate_by_region(dishes)

    # Track which dishes have been used (for overflow detection)
    used_count: dict[str, int] = {}
    # Track dishes used in the previous week (for spacing)
    recently_used: set[str] = set()

    week_results: list[tuple[str, ...]] = []

    for week_idx in range(weeks):
        week_state = _WeekState()

        # Build available pools (exclude dishes used this iteration unless we need reuse)
        available_eastern = [d for d in eastern_dishes if used_count.get(d.uid, 0) == 0]
        available_western = [d for d in western_dishes if used_count.get(d.uid, 0) == 0]
        all_dishes_list = list(dishes)
        available_all = [d for d in all_dishes_list if used_count.get(d.uid, 0) == 0]

        # Pick Eastern dishes
        for _ in range(eastern_per_week):
            # Try unused first, then fall back to all
            pool = available_eastern if available_eastern else eastern_dishes
            if not pool:
                break
            best = _pick_best(list(pool), week_state, recently_used)
            if best:
                week_state.add_dish(best)
                used_count[best.uid] = used_count.get(best.uid, 0) + 1
                if best in available_eastern:
                    available_eastern.remove(best)
                if best in available_all:
                    available_all.remove(best)

        # Pick Western dishes
        for _ in range(western_per_week):
            pool = available_western if available_western else western_dishes
            if not pool:
                break
            best = _pick_best(list(pool), week_state, recently_used)
            if best:
                week_state.add_dish(best)
                used_count[best.uid] = used_count.get(best.uid, 0) + 1
                if best in available_western:
                    available_western.remove(best)
                if best in available_all:
                    available_all.remove(best)

        # Fill remaining slots from any available dish (flexible fallback)
        while len(week_state.dish_uids) < per_week:
            pool = available_all if available_all else all_dishes_list
            if not pool:
                break
            # Exclude already picked this week
            pool = [d for d in pool if d.uid not in week_state.dish_uids]
            if not pool:
                break
            best = _pick_best(pool, week_state, recently_used)
            if best:
                week_state.add_dish(best)
                used_count[best.uid] = used_count.get(best.uid, 0) + 1
                if best in available_all:
                    available_all.remove(best)
            else:
                break

        week_results.append(tuple(week_state.dish_uids))
        recently_used = set(week_state.dish_uids)

    # Calculate discarded and reused
    all_input_uids = {d.uid for d in dishes}
    all_used_uids = {uid for week in week_results for uid in week}
    discarded = tuple(uid for uid in all_input_uids if uid not in all_used_uids)
    reused = tuple(uid for uid, count in used_count.items() if count > 1)

    return DistributionResult(
        weeks=tuple(week_results),
        discarded=discarded,
        reused=reused,
    )
