"""Meal plan analysis services.

Pure functions for analyzing variety, nutrition, and other metrics.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from meal_planning.catalogue.domain.enums import DishTag
from meal_planning.catalogue.repositories.protocols import DishRepository
from meal_planning.planning.domain.models import MonthlyPlan


@dataclass(frozen=True)
class VarietyReport:
    """Report on meal variety in a plan."""

    tag_distribution: dict[str, int]
    repeated_dishes: dict[str, int]  # dish_uid -> count (only if > 2)
    unique_dish_count: int
    total_scheduled_count: int
    variety_score: int  # 0-100

    @property
    def repetition_ratio(self) -> float:
        """Ratio of repeated to total dishes."""
        if self.total_scheduled_count == 0:
            return 0.0
        return len(self.repeated_dishes) / self.total_scheduled_count


def calculate_variety_score(
    unique_count: int, total_count: int, tag_counts: dict[str, int]
) -> int:
    """Calculate variety score (0-100).

    Factors:
    - Uniqueness: more unique dishes = higher score
    - Balance: even distribution across tags = higher score
    """
    if total_count == 0:
        return 100  # Empty plan is "perfectly varied"

    # Uniqueness factor (50% of score)
    uniqueness = (unique_count / total_count) * 50

    # Balance factor (50% of score)
    if len(tag_counts) == 0:
        balance = 50
    else:
        # Calculate how evenly distributed tags are
        tag_values = list(tag_counts.values())
        avg = sum(tag_values) / len(tag_values)
        if avg == 0:
            balance = 50
        else:
            # Lower deviation = higher balance score
            deviation = sum(abs(v - avg) for v in tag_values) / len(tag_values)
            balance = max(0, 50 - (deviation / avg) * 25)

    return int(uniqueness + balance)


def assess_variety(
    plan: MonthlyPlan,
    dish_repo: DishRepository,
) -> VarietyReport:
    """Analyze meal variety in a plan.

    Pure function that examines:
    - Distribution of dish tags (Eastern vs Western)
    - Repetition of specific dishes
    - Overall variety score

    Args:
        plan: Monthly plan to analyze.
        dish_repo: Repository to look up dish details.

    Returns:
        VarietyReport with variety metrics.
    """
    all_dish_uids = plan.all_scheduled_dish_uids()
    total_count = len(all_dish_uids)

    # Count occurrences
    dish_counts = Counter(all_dish_uids)
    unique_count = len(dish_counts)

    # Find repeated dishes (appearing more than 2 times)
    repeated = {uid: count for uid, count in dish_counts.items() if count > 2}

    # Count tag distribution
    tag_counts: dict[str, int] = {}
    for dish_uid in all_dish_uids:
        dish_result = dish_repo.get(dish_uid)
        if dish_result.is_err():
            continue

        dish = dish_result.unwrap()
        for tag in dish.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    variety_score = calculate_variety_score(unique_count, total_count, tag_counts)

    return VarietyReport(
        tag_distribution=tag_counts,
        repeated_dishes=repeated,
        unique_dish_count=unique_count,
        total_scheduled_count=total_count,
        variety_score=variety_score,
    )


def suggest_improvements(report: VarietyReport, dish_repo: DishRepository) -> list[str]:
    """Suggest improvements based on variety report.

    Args:
        report: Variety analysis report.
        dish_repo: Repository to look up dishes.

    Returns:
        List of improvement suggestions.
    """
    suggestions: list[str] = []

    # Check for excessive repetition
    for dish_uid, count in report.repeated_dishes.items():
        dish_result = dish_repo.get(dish_uid)
        if dish_result.is_ok():
            dish = dish_result.unwrap()
            suggestions.append(
                f"'{dish.name}' appears {count} times. Consider reducing to 1-2 times."
            )

    # Check tag imbalance
    if report.tag_distribution:
        max_tag = max(report.tag_distribution.values())
        min_tag = min(report.tag_distribution.values())
        if max_tag > min_tag * 2:
            dominant = [k for k, v in report.tag_distribution.items() if v == max_tag][0]
            suggestions.append(
                f"'{dominant}' dishes are dominant. Consider adding more variety."
            )

    # General score feedback
    if report.variety_score < 50:
        suggestions.append("Variety score is low. Try adding more unique dishes.")
    elif report.variety_score < 70:
        suggestions.append("Good variety, but room for improvement.")

    return suggestions
