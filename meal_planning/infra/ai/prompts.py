"""AI prompt templates.

Contains prompts used for AI-powered meal planning features.
"""

SYSTEM_PROMPT = """You are a helpful meal planning assistant. You help users plan their weekly and monthly meals.

## Your Capabilities
- View and manage a catalogue of ingredients and dishes
- Create and modify monthly meal plans (4 weeks per month)
- Generate shopping lists separated by bulk vs weekly purchase items
- Analyze meal variety and suggest improvements

## User Context
{user_context}

## Available Dishes
{available_dishes}

## Guidelines
1. Always consider the user's dietary preferences and constraints
2. Aim for variety - mix Eastern and Western dishes
3. Don't schedule the same dish more than 2-3 times per month
4. Consider ingredient reuse for efficiency (e.g., if buying spinach, use in multiple dishes)
5. Balance weekday convenience with weekend cooking enjoyment

When suggesting meals:
- Explain your reasoning
- Consider the user's preferences
- Balance variety with practicality
"""

SUGGEST_PLAN_PROMPT = """Please create a meal plan for {month}.

Consider:
1. User preferences: {context}
2. Available dishes: {dishes}
3. Aim for variety across the 4 weeks
4. Balance Eastern and Western cuisines if applicable

For each week (W1-W4), schedule dishes for:
- Weekday dinners (Mon-Fri)
- Weekend meals (Sat-Sun)

Provide a summary of your plan and reasoning.
"""

ANALYZE_VARIETY_PROMPT = """Analyze the variety in this meal plan for {month}:

{plan_summary}

Provide:
1. Tag distribution (Eastern vs Western, etc.)
2. Any dishes that repeat too often
3. Suggestions for improvement
4. Overall variety score assessment
"""

SHOPPING_LIST_PROMPT = """Generate a shopping list for Week {week} of {month}.

Scheduled dishes:
{week_schedule}

Separate items into:
1. Bulk items (buy monthly, stores well)
2. Weekly items (buy fresh)
"""


def format_system_prompt(user_context: str, available_dishes: str) -> str:
    """Format system prompt with context and dishes."""
    return SYSTEM_PROMPT.format(
        user_context=user_context or "No specific preferences set.",
        available_dishes=available_dishes or "No dishes in catalogue.",
    )


def format_suggest_plan_prompt(
    month: str, context: str, dishes: list[str]
) -> str:
    """Format meal suggestion prompt."""
    dishes_str = (
        "\n".join(f"- {d}" for d in dishes) if dishes else "No dishes available"
    )
    return SUGGEST_PLAN_PROMPT.format(
        month=month,
        context=context or "No specific preferences",
        dishes=dishes_str,
    )


def format_dish_list(dishes: list[dict]) -> str:
    """Format list of dishes for prompts."""
    if not dishes:
        return "No dishes available"

    lines = []
    for dish in dishes:
        tags = ", ".join(dish.get("tags", []))
        line = f"- {dish['name']}"
        if tags:
            line += f" ({tags})"
        lines.append(line)

    return "\n".join(lines)
