"""Context bounded context - user preferences and constraints."""

from meal_planning.core.context.models import UserContext
from meal_planning.core.context.aggregate import Preferences

__all__ = [
    # Entity
    "UserContext",
    # Aggregate
    "Preferences",
]
