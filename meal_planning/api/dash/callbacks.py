"""Dash callbacks for kanban-style meal planning."""

from __future__ import annotations

import uuid
from collections import Counter

from dash import callback, Output, Input, State, ALL, ctx, html
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc

from meal_planning.app import get_app_context, get_user_context
from meal_planning.core.catalogue.enums import Category, Cuisine
from meal_planning.core.catalogue.models import Dish
from meal_planning.api.dash.components import dish_card
from meal_planning.theme import CATEGORY_COLOR


def _get_context(session_id: str | None):
    """Get app context for session, falling back to default."""
    if session_id:
        return get_user_context(session_id)
    return get_app_context()


# =============================================================================
# Session Management
# =============================================================================


@callback(
    Output("session-id-store", "data"),
    Input("session-id-store", "data"),
)
def init_session(session_id):
    """Generate session ID on first visit, stored in localStorage."""
    if not session_id:
        return str(uuid.uuid4())
    raise PreventUpdate


def _filter_dishes(dishes, search: str | None, cuisine: str | None):
    """Filter dishes by search term and cuisine."""
    result = dishes

    if search:
        search_lower = search.lower()
        result = [d for d in result if search_lower in d.name.lower()]

    if cuisine and cuisine != "All":
        result = [d for d in result if d.cuisine.value == cuisine.lower()]

    return result


@callback(
    Output("shortlist-store", "data"),
    Input({"type": "add-dish", "uid": ALL}, "n_clicks"),
    Input({"type": "remove-dish", "uid": ALL}, "n_clicks"),
    State("shortlist-store", "data"),
    prevent_initial_call=True,
)
def update_shortlist_store(add_clicks, remove_clicks, current_shortlist):
    """Handle add/remove dish actions via pattern-matching callbacks."""
    triggered = ctx.triggered_id
    if not triggered or not isinstance(triggered, dict):
        return current_shortlist

    uid = triggered.get("uid")
    action = triggered.get("type")

    if not uid:
        return current_shortlist

    if action == "add-dish" and uid not in current_shortlist:
        return current_shortlist + [uid]
    elif action == "remove-dish" and uid in current_shortlist:
        return [u for u in current_shortlist if u != uid]

    return current_shortlist


@callback(
    Output("catalogue-cards", "children"),
    Output("catalogue-count", "children"),
    Output("shortlist-cards", "children"),
    Output("shortlist-count", "children"),
    Input("shortlist-store", "data"),
    Input("catalogue-search", "value"),
    Input("catalogue-cuisine-filter", "value"),
    Input("shortlist-search", "value"),
    Input("shortlist-cuisine-filter", "value"),
    State("session-id-store", "data"),
)
def render_columns(shortlist_uids, cat_search, cat_cuisine, sl_search, sl_cuisine, session_id):
    """Re-render both columns when selection or filters change."""
    app_ctx = _get_context(session_id)
    all_dishes = app_ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}

    # Ensure shortlist_uids is a list
    if shortlist_uids is None:
        shortlist_uids = []

    # Split dishes into available and shortlisted
    shortlisted = [dish_map[uid] for uid in shortlist_uids if uid in dish_map]
    available = [d for d in all_dishes if d.uid not in shortlist_uids]

    # Apply filters
    available_filtered = _filter_dishes(available, cat_search, cat_cuisine)
    shortlisted_filtered = _filter_dishes(shortlisted, sl_search, sl_cuisine)

    # Build card lists
    catalogue_cards = [dish_card(d, "right") for d in available_filtered]
    shortlist_cards = [dish_card(d, "left") for d in shortlisted_filtered]

    return (
        catalogue_cards,
        f"{len(available_filtered)} available",
        shortlist_cards,
        f"{len(shortlisted_filtered)} selected",
    )


@callback(
    # Modal state
    Output("results-modal", "opened"),
    # Hero score section
    Output("hero-score-number", "children"),
    Output("hero-score-bar", "value"),
    Output("hero-score-copy", "children"),
    # Colors and explore next
    Output("colors-bars", "children"),
    Output("explore-next", "children"),
    Output("category-tip", "children"),
    # Range section
    Output("cuisines-label", "children"),
    Output("cuisines-bar", "value"),
    Output("cuisines-copy", "children"),
    Output("balance-label", "children"),
    Output("balance-bar", "value"),
    Output("balance-copy", "children"),
    # Week cards
    Output("plan-weeks", "children"),
    Output("repetition-copy", "children"),
    Input("generate-btn", "n_clicks"),
    State("shortlist-store", "data"),
    State("session-id-store", "data"),
    prevent_initial_call=True,
)
def generate_plan(n_clicks, shortlist_uids, session_id):
    """Generate plan and diversity analysis from shortlisted dishes."""
    from meal_planning.copy.report_copy import (
        get_score_feedback,
        get_cuisine_feedback,
        get_balance_feedback,
        get_repetition_feedback,
        get_category_tip,
        get_category_examples,
        get_explore_intro,
    )

    # Empty state defaults
    empty_state = (
        True,  # Open modal
        "0%",  # hero score number
        0,  # hero score bar
        [html.P("Select some dishes to see your palette.", className="hero-score__body")],
        [],  # colors bars
        [html.P("Add dishes to discover what to explore.", className="explore-intro")],  # explore next
        "",  # category tip
        "Cuisines: 0 of 11",
        0,
        "Add dishes to see your cuisine range.",
        "Balance: 0% Eastern / 0% Western",
        50,
        "Add dishes to see your regional balance.",
        [],  # week cards
        "",  # repetition copy
    )

    if not shortlist_uids:
        return empty_state

    app_ctx = _get_context(session_id)
    all_dishes = app_ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}
    selected = [dish_map[uid] for uid in shortlist_uids if uid in dish_map]

    if not selected:
        return empty_state

    plan, result = app_ctx.planning.create_plan(
        name="Generated Plan",
        dishes=selected,
        weeks=4,
        dishes_per_week=4,
    )

    # ==========================================================================
    # Collect data for analysis
    # ==========================================================================
    week_cards = []
    category_counts = Counter()  # Total counts across all weeks
    all_categories_used = set()
    cuisine_counts = Counter()
    region_counts = Counter()
    unique_dishes = set()
    total_dish_slots = 0

    for i, week in enumerate(plan.weeks, 1):
        week_dishes = [dish_map[uid] for uid in week.dishes if uid in dish_map]

        # Build enhanced week card with category color dots
        dish_items = []
        for dish in week_dishes:
            unique_dishes.add(dish.uid)
            total_dish_slots += 1

            # Get first category color for the dot
            cat_color = "#E0E0E0"  # Default gray
            if dish.categories:
                first_cat = dish.categories[0]
                cat_color = CATEGORY_COLOR.get(first_cat, CATEGORY_COLOR[Category.GREENS]).bold

            dish_items.append(
                html.Div(
                    [
                        html.Span(
                            "",
                            className="dish-dot",
                            style={"backgroundColor": cat_color},
                        ),
                        html.Span(dish.name, className="dish-name"),
                    ],
                    className="dish-row",
                )
            )

        week_cards.append(
            dmc.Card(
                [
                    dmc.Text(f"Week {i}", fw=700, size="sm", c="dimmed"),
                    dmc.Divider(my="xs"),
                    html.Div(
                        dish_items if dish_items else [
                            dmc.Text("Empty", c="dimmed", size="sm")
                        ],
                        className="week-dishes",
                    ),
                ],
                withBorder=True,
                p="sm",
                className="week-card",
            )
        )

        # Collect category and cuisine data
        for dish in week_dishes:
            for cat in dish.categories:
                category_counts[cat.value] += 1
                all_categories_used.add(cat.value)
            cuisine_counts[dish.cuisine.value.title()] += 1
            region_counts[dish.region.value.title()] += 1

    # ==========================================================================
    # Calculate metrics
    # ==========================================================================
    total_categories = len(Category)
    categories_covered = len(all_categories_used)
    cat_score = round((categories_covered / total_categories) * 100)

    unique_cuisines = len(cuisine_counts)
    total_cuisines = len(Cuisine)

    eastern_count = region_counts.get("Eastern", 0)
    western_count = region_counts.get("Western", 0)
    total_region = eastern_count + western_count
    eastern_pct = round(eastern_count / total_region * 100) if total_region else 0
    western_pct = 100 - eastern_pct if total_region else 0

    # ==========================================================================
    # Build Hero Score Section
    # ==========================================================================
    hero_score_number = f"{cat_score}%"

    # Get all category names for missing list
    all_category_names = [cat.value.replace("_", " ").title() for cat in Category]
    used_category_names = [cat.replace("_", " ").title() for cat in all_categories_used]
    missing_categories = [name for name in all_category_names if name not in used_category_names]

    # Get verbose copy
    cuisine_list = list(cuisine_counts.keys())
    score_copy = get_score_feedback(cat_score, categories_covered, unique_cuisines, missing_categories)

    hero_copy = [
        html.H2(score_copy["headline"], className="hero-score__headline"),
        html.P(score_copy["body"], className="hero-score__body"),
    ]

    # ==========================================================================
    # Build Colors Bars (categories you're hitting)
    # ==========================================================================
    colors_bars = []
    max_count = max(category_counts.values()) if category_counts else 1

    # Sort by count descending
    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

    for cat_value, count in sorted_categories:
        cat_enum = Category(cat_value)
        cat_color = CATEGORY_COLOR.get(cat_enum, CATEGORY_COLOR[Category.GREENS])
        cat_label = cat_value.replace("_", " ").title()
        bar_pct = round((count / max_count) * 100)

        colors_bars.append(
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(cat_label, className="color-bar__label"),
                            html.Span(f"{count}", className="color-bar__count"),
                        ],
                        className="color-bar__header",
                    ),
                    html.Div(
                        html.Div(
                            className="color-bar__fill",
                            style={
                                "width": f"{bar_pct}%",
                                "backgroundColor": cat_color.bold,
                            },
                        ),
                        className="color-bar__track",
                        style={"backgroundColor": cat_color.muted},
                    ),
                ],
                className="color-bar",
            )
        )

    # ==========================================================================
    # Build Explore Next (missing categories with positive framing)
    # ==========================================================================
    explore_cards = []
    for cat in Category:
        if cat.value not in all_categories_used:
            cat_label = cat.value.replace("_", " ").title()
            cat_color = CATEGORY_COLOR.get(cat, CATEGORY_COLOR[Category.GREENS])
            examples = get_category_examples(cat.value)

            explore_cards.append(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("+", className="explore-card__plus"),
                                html.Span(cat_label, className="explore-card__label"),
                            ],
                            className="explore-card__header",
                        ),
                        html.Span(examples, className="explore-card__examples") if examples else None,
                    ],
                    className="explore-card",
                    style={
                        "backgroundColor": cat_color.muted,
                        "color": cat_color.bold,
                    },
                )
            )

    has_missing = len(explore_cards) > 0
    intro_text = get_explore_intro(has_missing)

    if explore_cards:
        explore_section = [
            html.P(intro_text, className="explore-intro"),
            html.Div(explore_cards, className="explore-cards"),
        ]
    else:
        explore_section = [
            html.P(intro_text, className="explore-empty"),
        ]

    # ==========================================================================
    # Category Tip
    # ==========================================================================
    top_category = sorted_categories[0][0] if sorted_categories else None
    category_tip = get_category_tip(top_category, categories_covered)

    # ==========================================================================
    # Build Range Section
    # ==========================================================================
    cuisines_label = f"Cuisines: {unique_cuisines} of {total_cuisines}"
    cuisines_bar_value = round((unique_cuisines / total_cuisines) * 100)
    cuisines_copy = get_cuisine_feedback(cuisine_list)

    # Balance now shows balance score (50/50 = 100%, 100/0 = 0%)
    balance_score, balance_copy = get_balance_feedback(eastern_pct, western_pct)
    balance_label = f"How balanced? ({eastern_pct}% Eastern / {western_pct}% Western)"
    balance_bar_value = balance_score

    # ==========================================================================
    # Repetition Copy
    # ==========================================================================
    repetition_copy = get_repetition_feedback(len(unique_dishes), total_dish_slots)

    return (
        True,  # Open modal
        hero_score_number,
        cat_score,  # hero score bar value
        hero_copy,
        colors_bars,
        explore_section,
        category_tip,
        cuisines_label,
        cuisines_bar_value,
        cuisines_copy,
        balance_label,
        balance_bar_value,
        balance_copy,
        week_cards,
        repetition_copy,
    )


# ============================================================================
# CRUD Modal Callbacks
# ============================================================================

@callback(
    Output("dish-modal", "opened"),
    Output("dish-modal", "title"),
    Output("dish-modal-mode", "data"),
    Output("dish-modal-uid", "data"),
    Output("dish-name", "value"),
    Output("dish-cuisine", "value"),
    Output("dish-categories", "value"),
    Output("dish-tags", "value"),
    Output("dish-recipe", "value"),
    Output("delete-dish-btn", "style"),
    Input("add-dish-btn", "n_clicks"),
    Input({"type": "edit-dish", "uid": ALL}, "n_clicks"),
    State("dish-modal", "opened"),
    State("session-id-store", "data"),
    prevent_initial_call=True,
)
def open_modal(add_clicks, edit_clicks, is_open, session_id):
    """Open modal for add or edit operations."""
    # Guard: prevent firing on initial load or when no real click occurred
    if not ctx.triggered or ctx.triggered[0]["value"] is None:
        raise PreventUpdate

    triggered = ctx.triggered_id

    # Close modal if clicking while open (shouldn't happen with modal)
    if is_open:
        return False, "Add Dish", "add", None, "", None, [], [], "", {"display": "none"}

    # Add new dish
    if triggered == "add-dish-btn":
        return (
            True,  # opened
            "Add Dish",  # title
            "add",  # mode
            None,  # uid
            "",  # name
            None,  # cuisine
            [],  # categories
            [],  # tags
            "",  # recipe
            {"display": "none"},  # hide delete button
        )

    # Edit existing dish
    if isinstance(triggered, dict) and triggered.get("type") == "edit-dish":
        uid = triggered.get("uid")
        if uid:
            # Load dish data
            app_ctx = _get_context(session_id)
            all_dishes = app_ctx.catalogue.list_dishes()
            dish = next((d for d in all_dishes if d.uid == uid), None)

            if dish:
                return (
                    True,  # opened
                    "Edit Dish",  # title
                    "edit",  # mode
                    uid,  # uid
                    dish.name,  # name
                    dish.cuisine.value,  # cuisine
                    [c.value for c in dish.categories],  # categories
                    list(dish.tags) if dish.tags else [],  # tags
                    dish.recipe_reference or "",  # recipe
                    {"display": "block"},  # show delete button
                )

    return False, "Add Dish", "add", None, "", None, [], [], "", {"display": "none"}


@callback(
    Output("dish-modal", "opened", allow_duplicate=True),
    Output("shortlist-store", "data", allow_duplicate=True),
    Input("save-dish-btn", "n_clicks"),
    State("dish-modal-mode", "data"),
    State("dish-modal-uid", "data"),
    State("dish-name", "value"),
    State("dish-cuisine", "value"),
    State("dish-categories", "value"),
    State("dish-tags", "value"),
    State("dish-recipe", "value"),
    State("shortlist-store", "data"),
    State("session-id-store", "data"),
    prevent_initial_call=True,
)
def save_dish(n_clicks, mode, uid, name, cuisine, categories, tags, recipe, shortlist, session_id):
    """Save dish (add new or update existing)."""
    if not name or not cuisine:
        # Don't close modal if required fields missing
        return True, shortlist

    app_ctx = _get_context(session_id)

    # Convert string values back to enums
    cuisine_enum = Cuisine(cuisine)
    category_enums = [Category(c) for c in (categories or [])]

    if mode == "edit" and uid:
        # Update existing dish
        dish = Dish(
            uid=uid,
            name=name,
            cuisine=cuisine_enum,
            categories=category_enums,
            tags=list(tags) if tags else [],
            recipe_reference=recipe or "",
        )
        app_ctx.catalogue.update_dish(dish)
    else:
        # Add new dish
        dish = Dish(
            name=name,
            cuisine=cuisine_enum,
            categories=category_enums,
            tags=list(tags) if tags else [],
            recipe_reference=recipe or "",
        )
        app_ctx.catalogue.add_dish(dish)

    # Persist to storage
    app_ctx.catalogue.save()

    return False, shortlist  # Close modal, keep shortlist unchanged


@callback(
    Output("dish-modal", "opened", allow_duplicate=True),
    Output("shortlist-store", "data", allow_duplicate=True),
    Input("delete-dish-btn", "n_clicks"),
    State("dish-modal-uid", "data"),
    State("shortlist-store", "data"),
    State("session-id-store", "data"),
    prevent_initial_call=True,
)
def delete_dish(n_clicks, uid, shortlist, session_id):
    """Delete dish from catalogue."""
    if not uid:
        return True, shortlist

    app_ctx = _get_context(session_id)
    app_ctx.catalogue.delete_dish(uid)
    app_ctx.catalogue.save()

    # Remove from shortlist if present
    new_shortlist = [u for u in shortlist if u != uid]

    return False, new_shortlist  # Close modal and update shortlist


# ============================================================================
# Info Modal Callback
# ============================================================================

@callback(
    Output("info-modal", "opened"),
    Input("info-btn", "n_clicks"),
    State("info-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_info_modal(n_clicks, is_open):
    """Toggle info modal on button click."""
    return not is_open


@callback(
    Output("get-started-modal", "opened"),
    Input("get-started-btn", "n_clicks"),
    State("get-started-modal", "opened"),
    prevent_initial_call=True,
)
def toggle_get_started_modal(n_clicks, is_open):
    """Toggle get started modal on button click."""
    return not is_open
