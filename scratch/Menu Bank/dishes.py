import enum
import typing as T
import uuid

import pydantic


class EnumDishTag(enum.StrEnum):
    EASTERN = "Eastern"
    WESTERN = "Western"


class EnumIngredientCategory(enum.StrEnum):
    GRAIN = "Grain"
    VEGETABLE = "Vegetable"
    PROTEIN = "Protein"


class EnumMealCategory(enum.StrEnum):
    TwoDayDinner = "2 Day Dinner"
    WeekendMeal = "Weekend Meal"
    DIYLunches = "DIY Lunch"


class VOAIContext(pydantic.BaseModel):
    uid: str = pydantic.Field(
        default_factory=lambda: f"AI-CONTEXT-{uuid.uuid4()}[:6]",
    )
    category: T.Optional[str] = None
    context: str


class VOIngredient(pydantic.BaseModel):
    uid: str = pydantic.Field(
        default_factory=lambda: f"INGREDIENT-{uuid.uuid4()}[:6]",
    )
    name: str
    tags: list[EnumIngredientCategory] = pydantic.Field(default_factory=list)


class VODish(pydantic.BaseModel):
    uid: str = pydantic.Field(
        default_factory=lambda: f"DISH-{uuid.uuid4()}[:6]",
    )
    name: str
    tags: list[str]
    ingredients: list[VOIngredient] = pydantic.Field(default_factory=list)


class VOMeal(pydantic.BaseModel):
    # uid: pydantic.UUID4
    # refactor so id is MEAL-5UID
    uid: str = pydantic.Field(
        default_factory=lambda: f"MEAL-{uuid.uuid4()}[:6]",
    )
    name: str
    dishes: list[VODish] = pydantic.Field(default_factory=list)
    tags: T.List[EnumMealCategory] = pydantic.Field(default_factory=list)


##################################################
# DEFAULT AI CONTEXT

VEGETARIAN = VOAIContext(
    context="We are vegetarian. We do not eat any meat, but do eat dairy ",
)
LOCATION = VOAIContext(
    context="We live in Johore Bahru, Malaysia. We prefer to eat with local ingredients.",
)

DEFAULT_AI_CONTEXT = [VEGETARIAN, LOCATION]

##################################################
# DEFAULT INGREDIENTS

POTATO = VOIngredient(
    name="Potato",
    tags=[EnumIngredientCategory.VEGETABLE],
)

DEFAULT_INGREDIENTS = [
    POTATO,
]


##################################################
# POPULAR DISHES

SHEPARDS_PIE = VODish(
    name="Shepard's Pie",
    tags=[EnumDishTag.EASTERN],
    ingredients=[POTATO],
)

KIMCHEE_FRIED_RICE = VODish(
    name="Kimchee Fried Rice",
    tags=[EnumDishTag.EASTERN],
)
THAI_FRIED_RICE = VODish(
    name="Thai Fried Rice",
    tags=[EnumDishTag.EASTERN],
)
INDO_FRIED_RICE = VODish(
    name="Indo Fried Rice",
    tags=[EnumDishTag.EASTERN],
)

STIR_FRY_VEG = VODish(
    name="Stir Fry Vegetables in Relevant Sauce",
    tags=[EnumDishTag.EASTERN],
)

FRIED_EGGS = VODish(
    name="Fried Eggs",
    tags=[EnumDishTag.EASTERN],
)

VEGETABLE_SOUP = VODish(
    name="Vegetable Soup",
    tags=[EnumDishTag.EASTERN],
)


DEFAULT_DISHES = [
    SHEPARDS_PIE,
]


##################################################
# POPULAR MEALS

fried_rice_and_veg = VOMeal(
    name="Fried Rice and Vegetables",
    dishes=[KIMCHEE_FRIED_RICE, STIR_FRY_VEG, FRIED_EGGS],
    tags=[EnumMealCategory.TwoDayDinner],
)
