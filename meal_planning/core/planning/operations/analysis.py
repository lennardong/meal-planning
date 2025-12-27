"""Meal plan analysis operations.

Pure functions for analyzing variety, nutrition, and other metrics.
These functions take domain objects as input and return analysis results.
No I/O operations - all data passed as arguments.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.planning.models import MealPlan


@dataclass(frozen=True)
class VarietyReport:
    """Report on meal variety in a plan."""

    cuisine_distribution: dict[str, int]  # cuisine -> count
    region_distribution: dict[str, int]  # region -> count
    category_distribution: dict[str, int]  # category -> count
    repeated_dishes: dict[str, int]  # dish_uid -> count (only if > 2)
    unique_dish_count: int
    total_dish_count: int
    variety_score: int  # 0-100

    @property
    def repetition_ratio(self) -> float:
        """Ratio of repeated to total dishes."""
        if self.total_dish_count == 0:
            return 0.0
        return len(self.repeated_dishes) / self.total_dish_count


def calculate_variety_score(
    unique_count: int,
    total_count: int,
    cuisine_counts: dict[str, int],
    region_counts: dict[str, int],
) -> int:
    """Calculate variety score (0-100).

    Factors:
    - Uniqueness: more unique dishes = higher score (40%)
    - Cuisine variety: more cuisines = higher score (30%)
    - Region balance: even East/West = higher score (30%)
    """
    if total_count == 0:
        return 100  # Empty plan is "perfectly varied"

    # Uniqueness factor (40% of score)
    uniqueness = (unique_count / total_count) * 40

    # Cuisine variety factor (30% of score)
    cuisine_count = len(cuisine_counts)
    max_cuisines = 11  # All available cuisines
    cuisine_score = min(30, (cuisine_count / max_cuisines) * 30)

    # Region balance factor (30% of score)
    eastern = region_counts.get("eastern", 0)
    western = region_counts.get("western", 0)
    total = eastern + western
    if total == 0:
        balance_score = 30
    else:
        # Perfect balance is 50/50
        ratio = min(eastern, western) / max(eastern, western) if max(eastern, western) > 0 else 1
        balance_score = ratio * 30

    return int(uniqueness + cuisine_score + balance_score)


def assess_variety(
    plan: MealPlan,
    dishes: Sequence[Dish],
) -> VarietyReport:
    """Analyze meal variety in a plan.

    Pure function that examines:
    - Distribution of cuisines and regions
    - Distribution of food categories
    - Repetition of specific dishes
    - Overall variety score

    Args:
        plan: Meal plan to analyze.
        dishes: All available dishes (for lookup).

    Returns:
        VarietyReport with variety metrics.
    """
    # Build lookup dictionary
    dish_by_uid = {d.uid: d for d in dishes}

    all_dish_uids = plan.all_dish_uids()
    total_count = len(all_dish_uids)

    # Count occurrences
    dish_counts = Counter(all_dish_uids)
    unique_count = len(dish_counts)

    # Find repeated dishes (appearing more than 2 times)
    repeated = {uid: count for uid, count in dish_counts.items() if count > 2}

    # Count distributions
    cuisine_counts: dict[str, int] = {}
    region_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}

    for dish_uid in all_dish_uids:
        dish = dish_by_uid.get(dish_uid)
        if dish is None:
            continue

        # Count cuisine
        cuisine = dish.cuisine.value
        cuisine_counts[cuisine] = cuisine_counts.get(cuisine, 0) + 1

        # Count region
        region = dish.region.value
        region_counts[region] = region_counts.get(region, 0) + 1

        # Count categories
        for cat in dish.categories:
            cat_name = cat.value
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

    variety_score = calculate_variety_score(
        unique_count, total_count, cuisine_counts, region_counts
    )

    return VarietyReport(
        cuisine_distribution=cuisine_counts,
        region_distribution=region_counts,
        category_distribution=category_counts,
        repeated_dishes=repeated,
        unique_dish_count=unique_count,
        total_dish_count=total_count,
        variety_score=variety_score,
    )


def suggest_improvements(
    report: VarietyReport,
    dishes: Sequence[Dish],
) -> list[str]:
    """Suggest improvements based on variety report.

    Args:
        report: Variety analysis report.
        dishes: All available dishes (for lookup).

    Returns:
        List of improvement suggestions.
    """
    # Build lookup dictionary
    dish_by_uid = {d.uid: d for d in dishes}

    suggestions: list[str] = []

    # Check for excessive repetition
    for dish_uid, count in report.repeated_dishes.items():
        dish = dish_by_uid.get(dish_uid)
        if dish is not None:
            suggestions.append(
                f"'{dish.name}' appears {count} times. Consider reducing to 1-2 times."
            )

    # Check region imbalance
    eastern = report.region_distribution.get("eastern", 0)
    western = report.region_distribution.get("western", 0)
    if eastern > 0 and western > 0:
        ratio = max(eastern, western) / min(eastern, western)
        if ratio > 2:
            dominant = "Eastern" if eastern > western else "Western"
            suggestions.append(
                f"{dominant} dishes are dominant ({max(eastern, western)} vs {min(eastern, western)}). "
                "Consider balancing regions."
            )

    # Check cuisine variety
    if len(report.cuisine_distribution) < 3:
        suggestions.append(
            f"Only {len(report.cuisine_distribution)} cuisine(s) used. "
            "Consider adding more variety."
        )

    # General score feedback
    if report.variety_score < 50:
        suggestions.append("Variety score is low. Try adding more unique dishes.")
    elif report.variety_score < 70:
        suggestions.append("Good variety, but room for improvement.")

    return suggestions
