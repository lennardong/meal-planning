"""Mantine component factories for kanban-style Dash app."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import dcc
from dash_iconify import DashIconify

from dash import html

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.catalogue.enums import Cuisine, Category
from meal_planning.theme import CUISINE_FLAG


# =============================================================================
# Tag Components (CSS-driven via data attributes)
# =============================================================================


def cuisine_flag(cuisine_value: str) -> html.Span:
    """Create a cuisine flag emoji. Compact, delightful."""
    try:
        cuisine = Cuisine(cuisine_value.lower())
        flag = CUISINE_FLAG.get(cuisine, "🍽️")
    except ValueError:
        flag = "🍽️"
    return html.Span(
        flag,
        className="card__flag",
        title=cuisine_value.title(),
    )


def category_tag(category_value: str) -> html.Span:
    """Create a category tag. Styling via CSS data attributes. Sentence case."""
    key = category_value.lower().replace(" ", "_")
    # Sentence case (capitalize first letter only)
    label = category_value.replace("_", " ").title()
    return html.Span(
        label,
        className="tag tag--sm tag--category",
        **{"data-category": key},
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


def dish_card(dish: Dish, direction: str = "right") -> html.Div:
    """Create a dish card. Styling via CSS classes.

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

    return html.Div(
        html.Div(
            [
                # Header row: title + flag + actions
                html.Div(
                    [
                        html.Span(dish.name, className="card__title"),
                        cuisine_flag(dish.cuisine.value),
                        html.Div(
                            [
                                dmc.ActionIcon(
                                    DashIconify(icon="mdi:pencil", width=14),
                                    id={"type": "edit-dish", "uid": dish.uid},
                                    variant="subtle",
                                    color="gray",
                                    size="xs",
                                ),
                                dmc.ActionIcon(
                                    DashIconify(icon=icon, width=16),
                                    id={"type": action_type, "uid": dish.uid},
                                    variant="light",
                                    color=action_color,
                                    size="sm",
                                ),
                            ],
                            className="card__actions",
                        ),
                    ],
                    className="card__header",
                ),
                # Category tags (show first 2) - these are the "colors"
                html.Div(
                    [category_tag(cat.value) for cat in dish.categories[:2]],
                    className="card__tags",
                ),
            ],
            className="card__content",
        ),
        className="card",
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
            className="chiclet chiclet--counter",
        ),
        mt="sm",
    )

    # Section chiclet label
    section_label = html.Span(
        title.upper(),
        className="chiclet chiclet--section",
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
    """Results modal - redesigned with hero score, verbose copy, and blind spots."""
    return dmc.Modal(
        id="results-modal",
        title="Your Palate Score",
        centered=True,
        size="85%",
        padding="lg",
        children=dmc.ScrollArea(
            dmc.Stack(
                [
                    # ==========================================================
                    # Section 1: Hero Score
                    # ==========================================================
                    html.Div(
                        [
                            # Large score number
                            html.Div(
                                id="hero-score-number",
                                className="hero-score__number",
                                children="0%",
                            ),
                            # Spectrum progress bar
                            dmc.Progress(
                                id="hero-score-bar",
                                value=0,
                                size="xl",
                                radius="xl",
                                color="saffron",
                                style={"marginBottom": "16px"},
                            ),
                            # Verbose copy block
                            html.Div(
                                id="hero-score-copy",
                                className="hero-score__copy",
                                children=[],
                            ),
                        ],
                        className="hero-score",
                    ),
                    # ==========================================================
                    # Section 2: Colors + Explore Next (side by side)
                    # ==========================================================
                    dmc.SimpleGrid(
                        [
                            # Left: What you're eating (categories you're hitting)
                            html.Div(
                                [
                                    html.H3("What you're eating", className="section-title"),
                                    html.Div(
                                        id="colors-bars",
                                        className="colors-section",
                                        children=[],
                                    ),
                                ],
                            ),
                            # Right: Try adding... (positive framing)
                            html.Div(
                                [
                                    html.H3("Try adding...", className="section-title"),
                                    html.Div(
                                        id="explore-next",
                                        className="explore-section",
                                        children=[],
                                    ),
                                ],
                            ),
                        ],
                        cols={"base": 1, "md": 2},
                        spacing="xl",
                    ),
                    # Contextual tip
                    html.Div(
                        id="category-tip",
                        className="category-tip",
                        children="",
                    ),
                    # ==========================================================
                    # Section 3: Your Range (Cuisines + Balance)
                    # ==========================================================
                    html.Div(
                        [
                            html.H3("How far you're traveling", className="section-title"),
                            # Cuisines
                            html.Div(
                                [
                                    html.Div(
                                        id="cuisines-label",
                                        className="range-label",
                                        children="Cuisines: 0 of 11",
                                    ),
                                    dmc.Progress(
                                        id="cuisines-bar",
                                        value=0,
                                        size="lg",
                                        radius="xl",
                                        color="grape",
                                    ),
                                    html.Div(
                                        id="cuisines-copy",
                                        className="range-copy",
                                        children="",
                                    ),
                                ],
                                className="range-metric",
                            ),
                            # Balance
                            html.Div(
                                [
                                    html.Div(
                                        id="balance-label",
                                        className="range-label",
                                        children="Balance: 0% Eastern / 0% Western",
                                    ),
                                    dmc.Progress(
                                        id="balance-bar",
                                        value=50,
                                        size="lg",
                                        radius="xl",
                                        color="blue",
                                    ),
                                    html.Div(
                                        id="balance-copy",
                                        className="range-copy",
                                        children="",
                                    ),
                                ],
                                className="range-metric",
                            ),
                        ],
                        className="range-section",
                    ),
                    # ==========================================================
                    # Section 4: Your Month (Enhanced Week Cards)
                    # ==========================================================
                    html.Div(
                        [
                            html.H3("Your menu this month", className="section-title"),
                            dmc.SimpleGrid(
                                id="plan-weeks",
                                cols={"base": 2, "md": 4},
                                spacing="md",
                                children=[],
                            ),
                            # Repetition observation
                            html.Div(
                                id="repetition-copy",
                                className="repetition-copy",
                                children="",
                            ),
                        ],
                    ),
                ],
                gap="xl",
            ),
            h="75vh",
            type="auto",
            offsetScrollbars=True,
            scrollbarSize=8,
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


def info_modal(modal_id: str, title: str, copy_key: str) -> dmc.Modal:
    """Reusable info modal that displays markdown content.

    Args:
        modal_id: Unique ID for the modal (e.g., "info-modal", "get-started-modal")
        title: Modal title displayed in header
        copy_key: Key to load content from copy folder (e.g., "app_about")
    """
    from meal_planning.copy import get_copy

    return dmc.Modal(
        id=modal_id,
        title=title,
        centered=True,
        size="lg",
        children=dmc.ScrollArea(
            dcc.Markdown(
                get_copy(copy_key),
                style={"fontSize": "14px", "lineHeight": "1.6"},
            ),
            h="60vh",
        ),
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
