"""Mantine component factories for kanban-style Dash app."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

from dash import html

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.catalogue.enums import Cuisine, Category


# =============================================================================
# Tag Color System
# =============================================================================

CUISINE_COLORS = {
    "chinese": {"bg": "#FFEBEE", "text": "#C62828"},
    "japanese": {"bg": "#FFF3E0", "text": "#E65100"},
    "korean": {"bg": "#FCE4EC", "text": "#AD1457"},
    "thai": {"bg": "#F3E5F5", "text": "#6A1B9A"},
    "indian": {"bg": "#FFFDE7", "text": "#F57F17"},
    "italian": {"bg": "#E8F5E9", "text": "#2E7D32"},
    "mexican": {"bg": "#E0F2F1", "text": "#00695C"},
    "western": {"bg": "#E8EAF6", "text": "#3949AB"},
    "mediterranean": {"bg": "#E1F5FE", "text": "#0277BD"},
    "vietnamese": {"bg": "#FFF8E1", "text": "#FF8F00"},
    "malay": {"bg": "#FBE9E7", "text": "#D84315"},
}

CATEGORY_COLORS = {
    "greens": {"bg": "#E8F5E9", "text": "#4A7C59"},
    "legumes": {"bg": "#EFEBE9", "text": "#8B5A2B"},
    "grains": {"bg": "#FFFDE7", "text": "#A68F00"},
    "fermented": {"bg": "#E0F7FA", "text": "#5BA4A4"},
    "alliums": {"bg": "#F3E5F5", "text": "#7B4B94"},
    "protein": {"bg": "#E3F2FD", "text": "#4A6FA5"},
    "fruits": {"bg": "#FCE4EC", "text": "#D46A84"},
    "nuts_seeds": {"bg": "#FFF3E0", "text": "#D4883E"},
    "dairy": {"bg": "#F5F5F5", "text": "#757575"},
    "red_orange_veg": {"bg": "#FFEBEE", "text": "#C1513D"},
    "cruciferous": {"bg": "#E8F5E9", "text": "#558B2F"},
    "root_veg": {"bg": "#EFEBE9", "text": "#6D4C41"},
    "mushrooms": {"bg": "#F3E5F5", "text": "#5D4037"},
    "herbs_spices": {"bg": "#E8F5E9", "text": "#33691E"},
    "eggs": {"bg": "#FFFDE7", "text": "#F9A825"},
    "seafood": {"bg": "#E1F5FE", "text": "#0288D1"},
    "slow_cooked": {"bg": "#FBE9E7", "text": "#BF360C"},
    "raw": {"bg": "#E8F5E9", "text": "#2E7D32"},
    "quick_cook": {"bg": "#FFF8E1", "text": "#FF8F00"},
}

DEFAULT_COLOR = {"bg": "#F5F5F5", "text": "#757575"}


def cuisine_tag(cuisine_value: str) -> html.Span:
    """Create a styled cuisine tag."""
    colors = CUISINE_COLORS.get(cuisine_value.lower(), DEFAULT_COLOR)
    return html.Span(
        cuisine_value.title(),
        style={
            "backgroundColor": colors["bg"],
            "color": colors["text"],
            "padding": "4px 10px",
            "borderRadius": "4px",
            "fontSize": "11px",
            "fontWeight": "500",
            "textTransform": "uppercase",
            "letterSpacing": "0.5px",
            "display": "inline-block",
        },
    )


def category_tag(category_value: str) -> html.Span:
    """Create a styled category tag."""
    # Normalize key (handle underscores and spaces)
    key = category_value.lower().replace(" ", "_")
    colors = CATEGORY_COLORS.get(key, DEFAULT_COLOR)
    return html.Span(
        category_value.replace("_", " ").title(),
        style={
            "backgroundColor": colors["bg"],
            "color": colors["text"],
            "padding": "3px 8px",
            "borderRadius": "4px",
            "fontSize": "10px",
            "fontWeight": "500",
            "textTransform": "uppercase",
            "letterSpacing": "0.3px",
            "display": "inline-block",
        },
    )


# Cache dish data at module level (loaded once on import)
_cached_dishes: list | None = None
_cached_cuisines: list | None = None


def _get_cached_data():
    """Get cached dish list and cuisines (loads once, reuses thereafter)."""
    global _cached_dishes, _cached_cuisines
    if _cached_dishes is None:
        from meal_planning.app import get_app_context
        ctx = get_app_context()
        _cached_dishes = ctx.catalogue.list_dishes()
        _cached_cuisines = ["All"] + sorted(set(d.cuisine.value for d in _cached_dishes))
    return _cached_dishes, _cached_cuisines


def dish_card(dish: Dish, direction: str = "right") -> dmc.Paper:
    """Create a compact dish card with transfer action button.

    Args:
        dish: The dish data
        direction: "right" (add to shortlist) or "left" (remove from shortlist)
    """
    # Determine action type and icon
    if direction == "right":
        icon = "mdi:chevron-right"
        action_type = "add-dish"
        action_color = "saffron"
    else:
        icon = "mdi:chevron-left"
        action_type = "remove-dish"
        action_color = "gray"

    # Category tags (show first 2 for compact view)
    category_tags = html.Div(
        [category_tag(cat.value) for cat in dish.categories[:2]],
        style={"display": "flex", "gap": "4px", "flexWrap": "wrap"},
    )

    return dmc.Paper(
        dmc.Stack(
            [
                # Row 1: Name + edit button + action button
                dmc.Group(
                    [
                        dmc.Text(dish.name, fw=600, size="sm", style={"flex": 1}),
                        dmc.ActionIcon(
                            DashIconify(icon="mdi:pencil", width=14),
                            id={"type": "edit-dish", "uid": dish.uid},
                            variant="subtle",
                            color="gray",
                            size="xs",
                            style={"opacity": 0.4},
                        ),
                        dmc.ActionIcon(
                            DashIconify(icon=icon, width=16),
                            id={"type": action_type, "uid": dish.uid},
                            variant="light",
                            color=action_color,
                            size="sm",
                        ),
                    ],
                    justify="space-between",
                    wrap="nowrap",
                ),
                # Row 2: Cuisine tag
                cuisine_tag(dish.cuisine.value),
                # Row 3: Category tags
                category_tags,
            ],
            gap=4,
        ),
        p="xs",
        radius="sm",
        withBorder=True,
        shadow="xs",
    )


def dish_column(title: str, column_id: str, direction: str) -> dmc.Card:
    """Create a filterable dish column.

    Args:
        title: Column title (e.g., "Catalogue" or "Shortlist")
        column_id: ID prefix for components (e.g., "catalogue" or "shortlist")
        direction: "right" for catalogue, "left" for shortlist
    """
    _, cuisines = _get_cached_data()

    # Filter controls
    filter_row = dmc.Group(
        [
            dmc.TextInput(
                id=f"{column_id}-search",
                placeholder="Search dishes...",
                leftSection=DashIconify(icon="mdi:magnify"),
                style={"flex": 1},
                size="sm",
            ),
            dmc.Select(
                id=f"{column_id}-cuisine-filter",
                data=cuisines,
                value="All",
                placeholder="Cuisine",
                w=130,
                size="sm",
                clearable=True,
            ),
        ],
        gap="xs",
        mt="md",
        mb="md",
    )

    # Dish cards container - auto-columns with offset scrollbar
    # Taller now that Results is in modal (70vh instead of 50vh)
    dish_cards = dmc.ScrollArea(
        dmc.SimpleGrid(
            id=f"{column_id}-cards",
            children=[],
            spacing="xs",
            verticalSpacing="xs",
            cols={"base": 1, "sm": 2, "lg": 3},
            p="xs",  # Padding to prevent edge clipping
        ),
        h="calc(70vh - 140px)",
        type="auto",
        offsetScrollbars=True,  # Reserve space for scrollbar
        scrollbarSize=8,  # Thinner scrollbar
    )

    # Footer with count (chiclet style)
    footer = dmc.Center(
        html.Span(
            "0 dishes",
            id=f"{column_id}-count",
            className="counter-chiclet",
        ),
        mt="sm",
    )

    # Section chiclet label
    section_label = html.Span(
        title.upper(),
        className="section-chiclet",
    )

    # Header with optional add button (only for catalogue)
    header_content = [section_label]
    if column_id == "catalogue":
        header_content = [
            dmc.Group(
                [
                    section_label,
                    add_dish_button(),
                ],
                justify="space-between",
            )
        ]

    return dmc.Card(
        [
            dmc.CardSection(
                header_content[0],
                inheritPadding=True,
                py="xs",
            ),
            filter_row,
            dish_cards,
            footer,
        ],
        withBorder=False,  # No border - cards inside are the visual focus
        shadow=None,
        bg="gray.0",  # Subtle background to define region
        p="md",
        style={"height": "100%"},
    )


def results_modal() -> dmc.Modal:
    """Results modal - simple single-page scrollable layout."""
    return dmc.Modal(
        id="results-modal",
        title="Your Palate Score",
        centered=True,
        size="85%",
        padding="lg",
        children=dmc.ScrollArea(
            dmc.Stack(
                [
                    # Row 1: Score summary (horizontal badges)
                    dmc.Group(
                        id="score-summary",
                        children=[],
                        justify="center",
                        gap="md",
                    ),
                    # Row 2: Week cards
                    dmc.SimpleGrid(
                        id="plan-weeks",
                        cols=4,
                        spacing="md",
                        children=[],
                    ),
                    # Row 3: Charts
                    dmc.SimpleGrid(
                        [
                            dcc.Graph(id="category-chart", style={"height": "300px"}),
                            dcc.Graph(id="cuisine-chart", style={"height": "300px"}),
                            dcc.Graph(id="region-chart", style={"height": "300px"}),
                        ],
                        cols=3,
                        spacing="md",
                    ),
                ],
                gap="xl",
            ),
            h="70vh",
            type="auto",
        ),
    )


def add_dish_button() -> dmc.ActionIcon:
    """Plus button to open add dish modal."""
    return dmc.ActionIcon(
        DashIconify(icon="mdi:plus", width=18),
        id="add-dish-btn",
        variant="light",
        color="blue",
        size="sm",
    )


def dish_modal() -> dmc.Modal:
    """Shared modal for add/edit dish operations."""
    # Build cuisine options from enum
    cuisine_options = [
        {"value": c.value, "label": c.value.title()}
        for c in Cuisine
    ]

    # Build category options from enum
    category_options = [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in Category
    ]

    return dmc.Modal(
        id="dish-modal",
        title="Add Dish",
        centered=True,
        size="md",
        children=dmc.Stack(
            [
                dmc.TextInput(
                    id="dish-name",
                    label="Name",
                    required=True,
                    placeholder="Enter dish name...",
                ),
                dmc.Select(
                    id="dish-cuisine",
                    label="Cuisine",
                    required=True,
                    data=cuisine_options,
                    placeholder="Select cuisine...",
                    searchable=True,
                ),
                dmc.MultiSelect(
                    id="dish-categories",
                    label="Categories",
                    data=category_options,
                    placeholder="Select categories...",
                    searchable=True,
                ),
                dmc.TagsInput(
                    id="dish-tags",
                    label="Tags (optional)",
                    placeholder="Type and press Enter to add tags...",
                ),
                dmc.TextInput(
                    id="dish-recipe",
                    label="Recipe Link (optional)",
                    placeholder="https://...",
                ),
                dmc.Group(
                    [
                        dmc.Button(
                            "Delete",
                            id="delete-dish-btn",
                            color="red",
                            variant="outline",
                            style={"display": "none"},
                        ),
                        dmc.Button(
                            "Save",
                            id="save-dish-btn",
                            color="blue",
                        ),
                    ],
                    justify="space-between",
                    mt="md",
                ),
            ],
            gap="sm",
        ),
    )
