"""Presentation theme tokens.

Single source of truth for colors, flags, and other presentation values.
Keep core domain pure - all presentation concerns live here.
"""

from dataclasses import dataclass

from meal_planning.core.catalogue.enums import Category, Cuisine


# =============================================================================
# Cuisine Flags (emoji display)
# =============================================================================

CUISINE_FLAG: dict[Cuisine, str] = {
    Cuisine.KOREAN: "🇰🇷",
    Cuisine.JAPANESE: "🇯🇵",
    Cuisine.CHINESE: "🇨🇳",
    Cuisine.THAI: "🇹🇭",
    Cuisine.VIETNAMESE: "🇻🇳",
    Cuisine.INDIAN: "🇮🇳",
    Cuisine.ITALIAN: "🇮🇹",
    Cuisine.FRENCH: "🇫🇷",
    Cuisine.AMERICAN: "🇺🇸",
    Cuisine.MEXICAN: "🇲🇽",
    Cuisine.MEDITERRANEAN: "🇬🇷",
}


# =============================================================================
# Category Colors
# =============================================================================


@dataclass(frozen=True)
class CategoryColor:
    """Color pair: muted for backgrounds, bold for text/charts."""

    muted: str
    bold: str


CATEGORY_COLOR: dict[Category, CategoryColor] = {
    Category.GREENS: CategoryColor("#E8F5E9", "#3D6B4A"),
    Category.LEGUMES: CategoryColor("#F5EFEA", "#7D6554"),
    Category.GRAINS: CategoryColor("#FFF8E7", "#8D7B4A"),
    Category.ALLIUMS: CategoryColor("#F3E5F5", "#6A5276"),
    Category.CRUCIFEROUS: CategoryColor("#E8F5E9", "#4A7040"),
    Category.FRESH_HERBS: CategoryColor("#E8F5E9", "#3D5A30"),
    Category.SEEDS: CategoryColor("#FFF3E8", "#9D7040"),
    Category.FERMENTED: CategoryColor("#E0F7FA", "#4A7C7C"),
    Category.ROOT_VEG: CategoryColor("#F0EBE7", "#5D4D44"),
    Category.DAIRY: CategoryColor("#F8F6F4", "#6B6560"),
}


# =============================================================================
# CSS Generation Helpers
# =============================================================================


def generate_category_css_vars() -> str:
    """Generate CSS variable definitions for injection into HTML head."""
    lines = []
    for cat, color in CATEGORY_COLOR.items():
        key = cat.value.replace("_", "-")
        lines.append(f"  --cat-{key}-bg: {color.muted};")
        lines.append(f"  --cat-{key}-text: {color.bold};")
    return ":root {\n" + "\n".join(lines) + "\n}"
