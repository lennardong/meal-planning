"""Planning operations - pure domain functions."""

from meal_planning.core.planning.operations.analysis import (
    VarietyReport,
    calculate_variety_score,
    assess_variety,
    suggest_improvements,
)
from meal_planning.core.planning.operations.distribution import (
    DistributionResult,
    distribute_dishes,
)

__all__ = [
    "VarietyReport",
    "calculate_variety_score",
    "assess_variety",
    "suggest_improvements",
    "DistributionResult",
    "distribute_dishes",
]
