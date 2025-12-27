"""Mantine component factories for kanban-style Dash app."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.catalogue.enums import Cuisine, Category


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
        color = "blue"
    else:
        icon = "mdi:chevron-left"
        action_type = "remove-dish"
        color = "red"

    # Region-based cuisine color
    region_color = "blue" if dish.region.value == "eastern" else "orange"

    # Category badges (show first 2 for compact view)
    category_badges = dmc.Group(
        [
            dmc.Badge(cat.value, size="xs", variant="light", color="gray")
            for cat in dish.categories[:2]
        ],
        gap=4,
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
                            color=color,
                            size="sm",
                        ),
                    ],
                    justify="space-between",
                    wrap="nowrap",
                ),
                # Row 2: Cuisine badge
                dmc.Badge(
                    dish.cuisine.value.title(),
                    size="xs",
                    color=region_color,
                ),
                # Row 3: Category badges
                category_badges,
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

    # Footer with count
    footer = dmc.Text(
        id=f"{column_id}-count",
        children="0 dishes",
        size="sm",
        c="dimmed",
        ta="center",
        mt="sm",
    )

    # Header with optional add button (only for catalogue)
    header_content = [dmc.Title(title, order=4)]
    if column_id == "catalogue":
        header_content = [
            dmc.Group(
                [
                    dmc.Title(title, order=4),
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
        title="Your Meal Plan Report",
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
