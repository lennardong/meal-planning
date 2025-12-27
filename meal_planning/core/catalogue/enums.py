"""Catalogue domain enumerations.

These enums define the valid values for dish and category classifications.
Using StrEnum for JSON serialization compatibility.
"""

from enum import StrEnum


class PurchaseType(StrEnum):
    """How a food category is typically purchased."""

    BULK = "bulk"  # Buy monthly, stores well
    WEEKLY = "weekly"  # Buy fresh each week


class Category(StrEnum):
    """Food type categories for dietary diversity tracking.

    These represent the types of foods, not nutritional categories.
    Used to ensure variety across a week's meal plan.
    """

    GREENS = "greens"  # Spinach, lettuce, bok choy
    LEGUMES = "legumes"  # Beans, lentils, chickpeas
    GRAINS = "grains"  # Rice, oats, wheat
    ALLIUMS = "alliums"  # Onion, garlic, leeks
    CRUCIFEROUS = "cruciferous"  # Broccoli, cabbage, cauliflower
    FRESH_HERBS = "fresh_herbs"  # Basil, cilantro, mint
    SEEDS = "seeds"  # Sesame, sunflower, pumpkin
    FERMENTED = "fermented"  # Kimchi, miso, sauerkraut
    ROOT_VEG = "root_veg"  # Potato, carrot, beet
    DAIRY = "dairy"  # Milk, cheese, yogurt


# Category → PurchaseType mapping (where to buy)
CATEGORY_PURCHASE_TYPE: dict[Category, PurchaseType] = {
    Category.GREENS: PurchaseType.WEEKLY,
    Category.LEGUMES: PurchaseType.BULK,
    Category.GRAINS: PurchaseType.BULK,
    Category.ALLIUMS: PurchaseType.WEEKLY,
    Category.CRUCIFEROUS: PurchaseType.WEEKLY,
    Category.FRESH_HERBS: PurchaseType.WEEKLY,
    Category.SEEDS: PurchaseType.BULK,
    Category.FERMENTED: PurchaseType.WEEKLY,
    Category.ROOT_VEG: PurchaseType.BULK,
    Category.DAIRY: PurchaseType.WEEKLY,
}


class Region(StrEnum):
    """Binary regional classification for balance constraint.

    Used for the hard constraint: 2 Eastern + 2 Western per week.
    """

    EASTERN = "eastern"  # Korean, Japanese, Chinese, Thai, Vietnamese, Indian
    WESTERN = "western"  # Italian, French, American, Mexican, Mediterranean


class Cuisine(StrEnum):
    """Granular cuisine types for novelty maximization.

    Used to ensure variety within each week (avoid same cuisine twice).
    """

    # Eastern cuisines
    KOREAN = "korean"
    JAPANESE = "japanese"
    CHINESE = "chinese"
    THAI = "thai"
    VIETNAMESE = "vietnamese"
    INDIAN = "indian"
    # Western cuisines
    ITALIAN = "italian"
    FRENCH = "french"
    AMERICAN = "american"
    MEXICAN = "mexican"
    MEDITERRANEAN = "mediterranean"


# Map cuisine to region for constraint checking
CUISINE_REGION: dict[Cuisine, Region] = {
    Cuisine.KOREAN: Region.EASTERN,
    Cuisine.JAPANESE: Region.EASTERN,
    Cuisine.CHINESE: Region.EASTERN,
    Cuisine.THAI: Region.EASTERN,
    Cuisine.VIETNAMESE: Region.EASTERN,
    Cuisine.INDIAN: Region.EASTERN,
    Cuisine.ITALIAN: Region.WESTERN,
    Cuisine.FRENCH: Region.WESTERN,
    Cuisine.AMERICAN: Region.WESTERN,
    Cuisine.MEXICAN: Region.WESTERN,
    Cuisine.MEDITERRANEAN: Region.WESTERN,
}
