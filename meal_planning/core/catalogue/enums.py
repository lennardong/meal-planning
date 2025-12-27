"""Catalogue domain enumerations.

These enums define the valid values for ingredient and dish classifications.
Using StrEnum for JSON serialization compatibility.
"""

from enum import StrEnum


class PurchaseType(StrEnum):
    """How an ingredient is typically purchased."""

    BULK = "bulk"  # Buy monthly, stores well
    WEEKLY = "weekly"  # Buy fresh each week


class IngredientTag(StrEnum):
    """Ingredient categories for classification."""

    GRAIN = "Grain"
    VEGETABLE = "Vegetable"
    PROTEIN = "Protein"
    DAIRY = "Dairy"
    SPICE = "Spice"
    OIL = "Oil"
    SAUCE = "Sauce"


class DishTag(StrEnum):
    """Dish style/cuisine classification."""

    EASTERN = "Eastern"
    WESTERN = "Western"
