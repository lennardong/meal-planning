"""Default vegetarian dishes for new users.

Domain knowledge: curated dishes with deterministic UIDs for stable identity.
These dishes represent a diverse selection of vegetarian options across
Eastern and Western cuisines, suitable for Indo-Chinese with Western upbringing.
"""

from typing import Final

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.catalogue.enums import Category, Cuisine


DEFAULTS_VERSION: Final[str] = "v1"


def _uid(prefix: str, name: str) -> str:
    """Generate deterministic UID: DEFAULT-chi-mapo-tofu."""
    slug = name.lower().replace(" ", "-").replace("'", "")
    return f"DEFAULT-{prefix}-{slug}"


DEFAULT_DISHES: Final[tuple[Dish, ...]] = (
    # =========================================================================
    # CHINESE (5 dishes)
    # =========================================================================
    Dish(
        uid=_uid("chi", "Mapo Tofu"),
        name="Mapo Tofu",
        categories=(Category.LEGUMES, Category.FERMENTED, Category.ALLIUMS),
        cuisine=Cuisine.CHINESE,
        recipe_reference="Silken tofu, doubanjiang, Sichuan peppercorns, scallions",
    ),
    Dish(
        uid=_uid("chi", "Vegetable Chow Mein"),
        name="Vegetable Chow Mein",
        categories=(Category.GRAINS, Category.GREENS, Category.ALLIUMS),
        cuisine=Cuisine.CHINESE,
        recipe_reference="Egg noodles, bok choy, cabbage, carrots, soy sauce",
    ),
    Dish(
        uid=_uid("chi", "Kung Pao Tofu"),
        name="Kung Pao Tofu",
        categories=(Category.LEGUMES, Category.ALLIUMS, Category.SEEDS),
        cuisine=Cuisine.CHINESE,
        recipe_reference="Firm tofu, peanuts, dried chilies, Sichuan peppercorns",
    ),
    Dish(
        uid=_uid("chi", "Vegetable Fried Rice"),
        name="Vegetable Fried Rice",
        categories=(Category.GRAINS, Category.GREENS, Category.ALLIUMS),
        cuisine=Cuisine.CHINESE,
        recipe_reference="Jasmine rice, eggs, peas, carrots, scallions",
    ),
    Dish(
        uid=_uid("chi", "Hot and Sour Soup"),
        name="Hot And Sour Soup",
        categories=(Category.LEGUMES, Category.FERMENTED, Category.GREENS),
        cuisine=Cuisine.CHINESE,
        recipe_reference="Tofu, wood ear mushrooms, bamboo shoots, rice vinegar",
    ),
    # =========================================================================
    # JAPANESE (5 dishes)
    # =========================================================================
    Dish(
        uid=_uid("jap", "Miso Soup"),
        name="Miso Soup",
        categories=(Category.FERMENTED, Category.LEGUMES, Category.GREENS),
        cuisine=Cuisine.JAPANESE,
        recipe_reference="White miso paste, silken tofu, wakame, scallions",
    ),
    Dish(
        uid=_uid("jap", "Vegetable Tempura"),
        name="Vegetable Tempura",
        categories=(Category.ROOT_VEG, Category.GREENS, Category.GRAINS),
        cuisine=Cuisine.JAPANESE,
        recipe_reference="Sweet potato, kabocha, shiso leaves, tempura batter",
    ),
    Dish(
        uid=_uid("jap", "Edamame Buddha Bowl"),
        name="Edamame Buddha Bowl",
        categories=(Category.GRAINS, Category.LEGUMES, Category.GREENS, Category.SEEDS),
        cuisine=Cuisine.JAPANESE,
        recipe_reference="Brown rice, edamame, avocado, pickled ginger, sesame",
    ),
    Dish(
        uid=_uid("jap", "Agedashi Tofu"),
        name="Agedashi Tofu",
        categories=(Category.LEGUMES, Category.GRAINS, Category.ALLIUMS),
        cuisine=Cuisine.JAPANESE,
        recipe_reference="Silken tofu, dashi broth, grated daikon, scallions",
    ),
    Dish(
        uid=_uid("jap", "Japanese Curry"),
        name="Japanese Curry",
        categories=(Category.ROOT_VEG, Category.GRAINS, Category.ALLIUMS),
        cuisine=Cuisine.JAPANESE,
        recipe_reference="Potato, carrots, onions, curry roux, rice",
    ),
    # =========================================================================
    # KOREAN (5 dishes)
    # =========================================================================
    Dish(
        uid=_uid("kor", "Kimchi Fried Rice"),
        name="Kimchi Fried Rice",
        categories=(Category.GRAINS, Category.FERMENTED, Category.ALLIUMS),
        cuisine=Cuisine.KOREAN,
        recipe_reference="Short-grain rice, aged kimchi, gochujang, sesame oil",
    ),
    Dish(
        uid=_uid("kor", "Bibimbap"),
        name="Bibimbap",
        categories=(Category.GRAINS, Category.GREENS, Category.FERMENTED, Category.SEEDS),
        cuisine=Cuisine.KOREAN,
        recipe_reference="Rice, spinach, bean sprouts, gochujang, fried egg",
    ),
    Dish(
        uid=_uid("kor", "Japchae"),
        name="Japchae",
        categories=(Category.GRAINS, Category.GREENS, Category.ALLIUMS, Category.SEEDS),
        cuisine=Cuisine.KOREAN,
        recipe_reference="Sweet potato noodles, spinach, carrots, sesame",
    ),
    Dish(
        uid=_uid("kor", "Sundubu Jjigae"),
        name="Sundubu Jjigae",
        categories=(Category.LEGUMES, Category.FERMENTED, Category.ALLIUMS),
        cuisine=Cuisine.KOREAN,
        recipe_reference="Soft tofu, gochugaru, kimchi, scallions, egg",
    ),
    Dish(
        uid=_uid("kor", "Kimbap"),
        name="Kimbap",
        categories=(Category.GRAINS, Category.GREENS, Category.ROOT_VEG, Category.SEEDS),
        cuisine=Cuisine.KOREAN,
        recipe_reference="Sushi rice, spinach, pickled radish, carrots, seaweed",
    ),
    # =========================================================================
    # THAI (4 dishes)
    # =========================================================================
    Dish(
        uid=_uid("tha", "Green Curry"),
        name="Thai Green Curry",
        categories=(Category.GREENS, Category.LEGUMES, Category.FRESH_HERBS),
        cuisine=Cuisine.THAI,
        recipe_reference="Coconut milk, green curry paste, tofu, Thai basil",
    ),
    Dish(
        uid=_uid("tha", "Pad Thai"),
        name="Pad Thai",
        categories=(Category.GRAINS, Category.LEGUMES, Category.ALLIUMS, Category.SEEDS),
        cuisine=Cuisine.THAI,
        recipe_reference="Rice noodles, tofu, bean sprouts, peanuts, lime",
    ),
    Dish(
        uid=_uid("tha", "Tom Yum Soup"),
        name="Tom Yum Soup",
        categories=(Category.GREENS, Category.FRESH_HERBS, Category.ALLIUMS),
        cuisine=Cuisine.THAI,
        recipe_reference="Lemongrass, galangal, kaffir lime, mushrooms, tofu",
    ),
    Dish(
        uid=_uid("tha", "Massaman Curry"),
        name="Massaman Curry",
        categories=(Category.ROOT_VEG, Category.LEGUMES, Category.SEEDS),
        cuisine=Cuisine.THAI,
        recipe_reference="Coconut milk, potatoes, tofu, peanuts, massaman paste",
    ),
    # =========================================================================
    # VIETNAMESE (3 dishes)
    # =========================================================================
    Dish(
        uid=_uid("vie", "Pho Chay"),
        name="Pho Chay",
        categories=(Category.GRAINS, Category.GREENS, Category.FRESH_HERBS, Category.ALLIUMS),
        cuisine=Cuisine.VIETNAMESE,
        recipe_reference="Rice noodles, vegetable broth, tofu, Thai basil, bean sprouts",
    ),
    Dish(
        uid=_uid("vie", "Banh Mi Chay"),
        name="Banh Mi Chay",
        categories=(Category.GRAINS, Category.LEGUMES, Category.ROOT_VEG, Category.FRESH_HERBS),
        cuisine=Cuisine.VIETNAMESE,
        recipe_reference="Baguette, lemongrass tofu, pickled carrots, cilantro",
    ),
    Dish(
        uid=_uid("vie", "Fresh Spring Rolls"),
        name="Fresh Spring Rolls",
        categories=(Category.GRAINS, Category.GREENS, Category.FRESH_HERBS),
        cuisine=Cuisine.VIETNAMESE,
        recipe_reference="Rice paper, vermicelli, lettuce, mint, peanut sauce",
    ),
    # =========================================================================
    # INDIAN (5 dishes)
    # =========================================================================
    Dish(
        uid=_uid("ind", "Dal Tadka"),
        name="Dal Tadka",
        categories=(Category.LEGUMES, Category.ALLIUMS, Category.FRESH_HERBS),
        cuisine=Cuisine.INDIAN,
        recipe_reference="Yellow lentils, cumin, garlic, cilantro, ghee",
    ),
    Dish(
        uid=_uid("ind", "Palak Paneer"),
        name="Palak Paneer",
        categories=(Category.GREENS, Category.DAIRY, Category.ALLIUMS),
        cuisine=Cuisine.INDIAN,
        recipe_reference="Spinach puree, paneer, cream, garam masala",
    ),
    Dish(
        uid=_uid("ind", "Chana Masala"),
        name="Chana Masala",
        categories=(Category.LEGUMES, Category.ALLIUMS, Category.FRESH_HERBS),
        cuisine=Cuisine.INDIAN,
        recipe_reference="Chickpeas, tomatoes, onions, garam masala, cilantro",
    ),
    Dish(
        uid=_uid("ind", "Aloo Gobi"),
        name="Aloo Gobi",
        categories=(Category.ROOT_VEG, Category.CRUCIFEROUS, Category.ALLIUMS),
        cuisine=Cuisine.INDIAN,
        recipe_reference="Potatoes, cauliflower, turmeric, cumin, ginger",
    ),
    Dish(
        uid=_uid("ind", "Vegetable Biryani"),
        name="Vegetable Biryani",
        categories=(Category.GRAINS, Category.ROOT_VEG, Category.ALLIUMS, Category.FRESH_HERBS),
        cuisine=Cuisine.INDIAN,
        recipe_reference="Basmati rice, mixed vegetables, saffron, fried onions",
    ),
    # =========================================================================
    # MEDITERRANEAN (4 dishes)
    # =========================================================================
    Dish(
        uid=_uid("med", "Falafel Wrap"),
        name="Falafel Wrap",
        categories=(Category.LEGUMES, Category.GREENS, Category.GRAINS, Category.FRESH_HERBS),
        cuisine=Cuisine.MEDITERRANEAN,
        recipe_reference="Chickpea falafel, pita, tahini, lettuce, tomatoes",
    ),
    Dish(
        uid=_uid("med", "Greek Salad"),
        name="Greek Salad",
        categories=(Category.GREENS, Category.DAIRY, Category.ALLIUMS),
        cuisine=Cuisine.MEDITERRANEAN,
        recipe_reference="Cucumber, tomatoes, feta, olives, red onion",
    ),
    Dish(
        uid=_uid("med", "Shakshuka"),
        name="Shakshuka",
        categories=(Category.LEGUMES, Category.ALLIUMS, Category.FRESH_HERBS),
        cuisine=Cuisine.MEDITERRANEAN,
        recipe_reference="Poached eggs, tomato sauce, bell peppers, cumin",
    ),
    Dish(
        uid=_uid("med", "Hummus Plate"),
        name="Hummus Plate",
        categories=(Category.LEGUMES, Category.SEEDS, Category.GRAINS),
        cuisine=Cuisine.MEDITERRANEAN,
        recipe_reference="Chickpea hummus, pita, olive oil, pine nuts",
    ),
    # =========================================================================
    # ITALIAN (3 dishes)
    # =========================================================================
    Dish(
        uid=_uid("ita", "Margherita Pizza"),
        name="Margherita Pizza",
        categories=(Category.GRAINS, Category.DAIRY, Category.FRESH_HERBS),
        cuisine=Cuisine.ITALIAN,
        recipe_reference="Pizza dough, tomato sauce, mozzarella, fresh basil",
    ),
    Dish(
        uid=_uid("ita", "Pasta Primavera"),
        name="Pasta Primavera",
        categories=(Category.GRAINS, Category.GREENS, Category.ALLIUMS),
        cuisine=Cuisine.ITALIAN,
        recipe_reference="Penne, zucchini, bell peppers, cherry tomatoes, garlic",
    ),
    Dish(
        uid=_uid("ita", "Caprese Salad"),
        name="Caprese Salad",
        categories=(Category.DAIRY, Category.FRESH_HERBS),
        cuisine=Cuisine.ITALIAN,
        recipe_reference="Fresh mozzarella, tomatoes, basil, balsamic glaze",
    ),
    # =========================================================================
    # MEXICAN (3 dishes)
    # =========================================================================
    Dish(
        uid=_uid("mex", "Black Bean Tacos"),
        name="Black Bean Tacos",
        categories=(Category.LEGUMES, Category.GRAINS, Category.GREENS, Category.ALLIUMS),
        cuisine=Cuisine.MEXICAN,
        recipe_reference="Corn tortillas, black beans, cabbage, salsa, lime",
    ),
    Dish(
        uid=_uid("mex", "Veggie Burrito Bowl"),
        name="Veggie Burrito Bowl",
        categories=(Category.GRAINS, Category.LEGUMES, Category.GREENS),
        cuisine=Cuisine.MEXICAN,
        recipe_reference="Cilantro lime rice, black beans, corn, guacamole",
    ),
    Dish(
        uid=_uid("mex", "Cheese Quesadilla"),
        name="Cheese Quesadilla",
        categories=(Category.GRAINS, Category.DAIRY, Category.ALLIUMS),
        cuisine=Cuisine.MEXICAN,
        recipe_reference="Flour tortilla, cheddar, peppers, onions, salsa",
    ),
    # =========================================================================
    # FRENCH (2 dishes)
    # =========================================================================
    Dish(
        uid=_uid("fre", "Ratatouille"),
        name="Ratatouille",
        categories=(Category.GREENS, Category.ROOT_VEG, Category.ALLIUMS, Category.FRESH_HERBS),
        cuisine=Cuisine.FRENCH,
        recipe_reference="Eggplant, zucchini, tomatoes, bell peppers, herbs de Provence",
    ),
    Dish(
        uid=_uid("fre", "French Onion Soup"),
        name="French Onion Soup",
        categories=(Category.ALLIUMS, Category.GRAINS, Category.DAIRY),
        cuisine=Cuisine.FRENCH,
        recipe_reference="Caramelized onions, vegetable broth, crusty bread, gruyere",
    ),
    # =========================================================================
    # AMERICAN (1 dish)
    # =========================================================================
    Dish(
        uid=_uid("ame", "Mac and Cheese"),
        name="Mac And Cheese",
        categories=(Category.GRAINS, Category.DAIRY),
        cuisine=Cuisine.AMERICAN,
        recipe_reference="Elbow pasta, cheddar cheese sauce, breadcrumbs",
    ),
)


# Derived lookup - computed once at import
DEFAULT_DISHES_BY_UID: Final[dict[str, Dish]] = {
    d.uid: d for d in DEFAULT_DISHES
}


def get_default_dishes() -> tuple[Dish, ...]:
    """Get all default dishes."""
    return DEFAULT_DISHES


def is_default_dish(uid: str) -> bool:
    """Check if UID represents a default dish."""
    return uid.startswith("DEFAULT-")
