"""Application services layer.

This layer contains:
- Port definitions (interfaces for infrastructure)
- Application services (orchestrate domain operations with I/O)

Services handle:
- JSON serialization/deserialization
- User-scoped key construction for blob storage
- Coordination between multiple domain operations
"""

from meal_planning.services.catalogue import CatalogueService
from meal_planning.services.planning import PlanningService
from meal_planning.services.context import ContextService
from meal_planning.services.shopping import ShoppingService
from meal_planning.services.analysis import AnalysisService
from meal_planning.services.ai_assistant import AIAssistantService

__all__ = [
    "CatalogueService",
    "PlanningService",
    "ContextService",
    "ShoppingService",
    "AnalysisService",
    "AIAssistantService",
]
