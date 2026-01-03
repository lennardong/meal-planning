"""Dynamic copy for the Palate Score report.

Voice: Like a friend who's into food but not annoying about it.
Tone: Direct, warm, specific, playful when it fits.
No wellness jargon. No empty praise. Just honest observations that feel personal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from meal_planning.core.catalogue.enums import Category, Cuisine


# =============================================================================
# Section Titles - Conversational, Not Labels
# =============================================================================

SECTION_TITLES = {
    "colors": "What you're eating",
    "explore": "Try adding...",
    "range": "How far you're traveling",
    "month": "Your menu this month",
}


# =============================================================================
# Score Feedback - Verbose, Friend-Style
# =============================================================================

SCORE_FEEDBACK = {
    "high": {  # 75%+
        "headline": "{score}%? That's genuinely impressive.",
        "body": (
            "You're hitting {colors} different food groups and rotating through {cuisines} cuisines. "
            "That's the kind of variety your microbiome dreams about. "
            "Most people eat the same 10 things on repeat — you're not most people. Keep this up."
        ),
    },
    "medium": {  # 50-74%
        "headline": "Not bad — you're on your way.",
        "body": (
            "You've got {colors} colors covered and {cuisines} cuisines in the mix. "
            "That's a solid foundation, but there's room to grow. "
            "You're missing {missing_categories} — adding even one of those would make a real difference."
        ),
    },
    "low": {  # <50%
        "headline": "Let's be honest — this is narrow.",
        "body": (
            "You're repeating the same foods, hitting only {colors} of 10 categories. "
            "Your gut's getting bored. But here's the thing: small changes make a big difference. "
            "Check out the suggestions below — even one new ingredient helps."
        ),
    },
}


# =============================================================================
# Category Examples - For "Explore Next" Section
# =============================================================================

CATEGORY_EXAMPLES = {
    "greens": "spinach, kale, bok choy",
    "legumes": "lentils, chickpeas, black beans",
    "grains": "quinoa, brown rice, oats",
    "alliums": "garlic, onions, leeks",
    "cruciferous": "broccoli, cabbage, cauliflower",
    "fresh_herbs": "basil, cilantro, mint",
    "seeds": "sesame, pumpkin, sunflower",
    "fermented": "kimchi, miso, yogurt",
    "root_veg": "carrots, beets, sweet potato",
    "dairy": "cheese, yogurt, milk",
}


# =============================================================================
# Cuisine Feedback - Chatty, Encouraging
# =============================================================================

CUISINE_FEEDBACK = {
    "none": "No cuisines tracked yet. Time to start exploring!",
    "single": (
        "Just {cuisine} this month. Nothing wrong with that, but your microbiome "
        "would love a change of scenery."
    ),
    "few": (
        "{count} cuisines in rotation. You're getting there — "
        "the world has so many flavors to explore."
    ),
    "varied": (
        "{count} different cuisines! You're taking your gut on a world tour."
    ),
}


# =============================================================================
# Region Balance Feedback - Based on Balance Score
# Balance score = 100 - abs(eastern_pct - 50) * 2
# 50/50 = 100% balanced, 100/0 = 0% balanced
# =============================================================================

BALANCE_FEEDBACK = {
    "perfect": (
        "Perfect balance — half Eastern, half Western. "
        "Your microbiome is living its best life."
    ),
    "good": (
        "Pretty good balance at {score}%. "
        "You're giving your gut a taste of both worlds."
    ),
    "leaning": (
        "Leaning {dominant} at {pct}%. "
        "A few {opposite} dishes would round things out nicely."
    ),
    "heavy": (
        "Heavily {dominant} this month. "
        "Your gut craves variety — try mixing in some {opposite} dishes."
    ),
    "all_one": (
        "All {dominant} this month. Nothing wrong with a theme, but your microbiome "
        "would love a change of scenery. How about some {suggestions}?"
    ),
}

# Suggestions for opposite region
REGION_SUGGESTIONS = {
    "eastern": "pasta, tacos, or Mediterranean",
    "western": "miso soup, pad thai, or stir fry",
}


# =============================================================================
# Repetition Feedback - Warm, No Snark
# =============================================================================

REPETITION_FEEDBACK = {
    "same_dish": (
        "Same dish appearing across weeks — comfort food is great, "
        "but your gut might appreciate some novelty."
    ),
    "few_dishes": (
        "A small rotation of favorites here. Nothing wrong with that, "
        "but there's room to explore."
    ),
    "varied": (
        "Nice variety across weeks — you're keeping things interesting."
    ),
}


# =============================================================================
# Category Tips - Verbose, Contextual
# =============================================================================

CATEGORY_TIPS_BY_COUNT = {
    "high": (
        "You're covering a lot of ground — {count} different food groups. "
        "That's the kind of variety your gut bacteria throw parties for."
    ),
    "medium": (
        "Solid foundation with {count} categories. "
        "Add a couple more and you'll really be cooking."
    ),
    "low": (
        "Just {count} food groups so far. "
        "Your gut's capable of so much more variety."
    ),
}

CATEGORY_TIPS_BY_TYPE = {
    "legumes": (
        "Legumes are doing the heavy lifting here. Great for fiber — "
        "now try adding some greens or fermented foods."
    ),
    "fermented": (
        "Fermented foods are your star player. Excellent for gut bacteria. "
        "Keep it up, and maybe add some variety in other categories."
    ),
    "alliums": (
        "Lots of alliums — onion, garlic, leeks. Flavor boosters for sure, "
        "but you'll want more variety in the other food groups too."
    ),
    "greens": (
        "Good on greens! Now add some fermented foods or legumes "
        "for the full spectrum."
    ),
    "grains": (
        "Grains are your base. Round things out with some color "
        "from other categories — greens, legumes, fermented."
    ),
    "default": (
        "You're covering ground, but there's more territory to explore. "
        "Check out the suggestions above."
    ),
}


# =============================================================================
# Explore Section Copy
# =============================================================================

EXPLORE_INTRO = "These are the food groups you haven't touched yet. Even adding one makes a difference."

EXPLORE_INTRO_NONE = "No gaps here — you're covering all your colors. Nice work."


# =============================================================================
# Helper Functions
# =============================================================================

def get_section_title(section: str) -> str:
    """Get conversational section title.

    Args:
        section: Section key (colors, explore, range, month)

    Returns:
        Conversational title string
    """
    return SECTION_TITLES.get(section, section.title())


def get_score_level(score: int) -> str:
    """Get the score level key based on percentage."""
    if score >= 75:
        return "high"
    elif score >= 50:
        return "medium"
    return "low"


def get_score_feedback(
    score: int,
    colors_count: int,
    cuisines_count: int,
    missing_categories: list[str],
) -> dict[str, str]:
    """Get headline and body copy for a given score.

    Args:
        score: Palate score percentage (0-100)
        colors_count: Number of categories covered
        cuisines_count: Number of cuisines used
        missing_categories: List of category names not covered

    Returns:
        Dict with 'headline' and 'body' keys
    """
    level = get_score_level(score)
    template = SCORE_FEEDBACK[level]

    # Format missing categories naturally
    if len(missing_categories) == 0:
        missing_str = "nothing"
    elif len(missing_categories) == 1:
        missing_str = missing_categories[0].lower()
    elif len(missing_categories) == 2:
        missing_str = f"{missing_categories[0].lower()} and {missing_categories[1].lower()}"
    else:
        # For many missing, just show first 2-3
        shown = missing_categories[:3]
        missing_str = f"{', '.join(c.lower() for c in shown[:-1])}, and {shown[-1].lower()}"

    return {
        "headline": template["headline"].format(score=score),
        "body": template["body"].format(
            colors=colors_count,
            cuisines=cuisines_count,
            missing_categories=missing_str,
        ),
    }


def get_cuisine_feedback(cuisines: list[str]) -> str:
    """Get feedback copy for cuisine variety.

    Args:
        cuisines: List of cuisine names used

    Returns:
        Feedback string
    """
    count = len(cuisines)
    if count == 0:
        return CUISINE_FEEDBACK["none"]
    elif count == 1:
        return CUISINE_FEEDBACK["single"].format(cuisine=cuisines[0])
    elif count <= 3:
        return CUISINE_FEEDBACK["few"].format(count=count)
    else:
        return CUISINE_FEEDBACK["varied"].format(count=count)


def get_balance_score(eastern_pct: int) -> int:
    """Calculate balance score from Eastern percentage.

    50/50 split = 100% balanced (perfect)
    100/0 or 0/100 = 0% balanced (all one region)

    Formula: balance_score = 100 - abs(eastern_pct - 50) * 2

    Args:
        eastern_pct: Percentage of Eastern cuisine dishes (0-100)

    Returns:
        Balance score (0-100) where 100 is perfect balance
    """
    return 100 - abs(eastern_pct - 50) * 2


def get_balance_feedback(eastern_pct: int, western_pct: int) -> tuple[int, str]:
    """Get balance score and feedback copy for region balance.

    Args:
        eastern_pct: Percentage of Eastern cuisine dishes
        western_pct: Percentage of Western cuisine dishes

    Returns:
        Tuple of (balance_score, feedback_string)
    """
    balance_score = get_balance_score(eastern_pct)

    # Determine dominant region
    if eastern_pct > western_pct:
        dominant = "Eastern"
        opposite = "Western"
        pct = eastern_pct
    else:
        dominant = "Western"
        opposite = "Eastern"
        pct = western_pct

    suggestions = REGION_SUGGESTIONS.get(opposite.lower(), "dishes from the other region")

    if balance_score == 100:
        feedback = BALANCE_FEEDBACK["perfect"]
    elif balance_score >= 80:
        feedback = BALANCE_FEEDBACK["good"].format(score=balance_score)
    elif balance_score >= 40:
        feedback = BALANCE_FEEDBACK["leaning"].format(
            dominant=dominant, pct=pct, opposite=opposite
        )
    elif balance_score > 0:
        feedback = BALANCE_FEEDBACK["heavy"].format(
            dominant=dominant, opposite=opposite
        )
    else:
        feedback = BALANCE_FEEDBACK["all_one"].format(
            dominant=dominant, suggestions=suggestions
        )

    return balance_score, feedback


def get_repetition_feedback(unique_dishes: int, total_dishes: int) -> str:
    """Get feedback copy for dish repetition.

    Args:
        unique_dishes: Number of unique dishes in the plan
        total_dishes: Total number of dish slots in the plan

    Returns:
        Feedback string
    """
    if total_dishes == 0:
        return ""

    ratio = unique_dishes / total_dishes

    if ratio <= 0.25:  # Same dish or very few
        return REPETITION_FEEDBACK["same_dish"]
    elif ratio <= 0.5:
        return REPETITION_FEEDBACK["few_dishes"]
    else:
        return REPETITION_FEEDBACK["varied"]


def get_category_tip(top_category: str | None, categories_covered: int) -> str:
    """Get a contextual tip based on category coverage.

    Args:
        top_category: The category with the most dishes (lowercase)
        categories_covered: Total number of categories covered

    Returns:
        Tip string
    """
    # First, check coverage level
    if categories_covered >= 7:
        return CATEGORY_TIPS_BY_COUNT["high"].format(count=categories_covered)
    elif categories_covered >= 4:
        return CATEGORY_TIPS_BY_COUNT["medium"].format(count=categories_covered)
    elif categories_covered >= 1:
        # Low coverage - check if there's a dominant category to comment on
        if top_category and top_category.lower() in CATEGORY_TIPS_BY_TYPE:
            return CATEGORY_TIPS_BY_TYPE[top_category.lower()]
        return CATEGORY_TIPS_BY_COUNT["low"].format(count=categories_covered)

    return CATEGORY_TIPS_BY_TYPE["default"]


def get_category_examples(category: str) -> str:
    """Get example foods for a category.

    Args:
        category: Category name (lowercase, with underscores)

    Returns:
        Comma-separated examples string
    """
    key = category.lower().replace(" ", "_")
    return CATEGORY_EXAMPLES.get(key, "")


def get_explore_intro(has_missing: bool) -> str:
    """Get intro copy for the Explore Next section.

    Args:
        has_missing: Whether there are missing categories

    Returns:
        Intro string
    """
    return EXPLORE_INTRO if has_missing else EXPLORE_INTRO_NONE
