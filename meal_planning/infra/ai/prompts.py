"""AI prompt templates.

Contains prompts used for AI-powered meal planning features.
"""

SYSTEM_PROMPT = """You are a helpful meal planning assistant. You help users plan their weekly meals.

## Your Capabilities
- View and manage a catalogue of dishes
- Create meal plans for N weeks using the shortlist
- Analyze meal variety and suggest improvements

## User Context
{user_context}

## Available Dishes
{available_dishes}

## Guidelines
1. Always consider the user's dietary preferences and constraints
2. Aim for variety - mix Eastern and Western dishes
3. Don't schedule the same dish more than 2-3 times per plan
4. Consider ingredient reuse for efficiency

When suggesting meals:
- Explain your reasoning
- Consider the user's preferences
- Balance variety with practicality
"""

SUGGEST_PLAN_PROMPT = """Please suggest a {weeks}-week meal plan called '{plan_name}'.

Consider:
1. User preferences: {context}
2. Available dishes: {dishes}
3. Aim for variety across the weeks
4. Balance Eastern and Western cuisines if applicable

Provide a summary of your plan and reasoning.
"""

ANALYZE_VARIETY_PROMPT = """Analyze the variety in this meal plan:

{plan_summary}

Provide:
1. Cuisine distribution
2. Region balance (Eastern vs Western)
3. Any dishes that repeat too often
4. Suggestions for improvement
5. Overall variety score assessment
"""


def format_system_prompt(user_context: str, available_dishes: str) -> str:
    """Format system prompt with context and dishes."""
    return SYSTEM_PROMPT.format(
        user_context=user_context or "No specific preferences set.",
        available_dishes=available_dishes or "No dishes in catalogue.",
    )


def format_suggest_plan_prompt(
    plan_name: str, weeks: int, context: str, dishes: list[str]
) -> str:
    """Format meal suggestion prompt."""
    dishes_str = (
        "\n".join(f"- {d}" for d in dishes) if dishes else "No dishes available"
    )
    return SUGGEST_PLAN_PROMPT.format(
        plan_name=plan_name,
        weeks=weeks,
        context=context or "No specific preferences",
        dishes=dishes_str,
    )


def format_dish_list(dishes: list[dict]) -> str:
    """Format list of dishes for prompts."""
    if not dishes:
        return "No dishes available"

    lines = []
    for dish in dishes:
        cuisine = dish.get("cuisine", "")
        region = dish.get("region", "")
        categories = ", ".join(dish.get("categories", []))
        line = f"- {dish['name']}"
        if cuisine:
            line += f" ({cuisine}"
            if region:
                line += f", {region}"
            line += ")"
        if categories:
            line += f" [{categories}]"
        lines.append(line)

    return "\n".join(lines)
