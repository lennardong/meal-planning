"""Dash callbacks for kanban-style meal planning."""

from __future__ import annotations

from collections import Counter

from dash import callback, Output, Input, State, ALL, ctx
from dash.exceptions import PreventUpdate
import dash_mantine_components as dmc
import plotly.express as px

from meal_planning.app import get_app_context
from meal_planning.core.catalogue.enums import Category, Cuisine
from meal_planning.core.catalogue.models import Dish
from meal_planning.api.dash.components import dish_card


def _get_dishes():
    """Get all dishes from catalogue."""
    app_ctx = get_app_context()
    return app_ctx.catalogue.list_dishes()


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
)
def render_columns(shortlist_uids, cat_search, cat_cuisine, sl_search, sl_cuisine):
    """Re-render both columns when selection or filters change."""
    all_dishes = _get_dishes()
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
    Output("results-modal", "opened"),
    Output("plan-weeks", "children"),
    Output("score-summary", "children"),
    Output("category-chart", "figure"),
    Output("cuisine-chart", "figure"),
    Output("region-chart", "figure"),
    Input("generate-btn", "n_clicks"),
    State("shortlist-store", "data"),
    prevent_initial_call=True,
)
def generate_plan(n_clicks, shortlist_uids):
    """Generate plan and diversity analysis from shortlisted dishes."""
    empty_fig = px.pie(values=[1], names=["No data"], title="No data")
    empty_fig.update_layout(showlegend=False, margin=dict(t=40, b=20, l=20, r=20))

    empty_summary = [dmc.Text("Select dishes first", c="dimmed", size="sm")]

    if not shortlist_uids:
        return True, [], empty_summary, empty_fig, empty_fig, empty_fig

    app_ctx = get_app_context()
    all_dishes = app_ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}
    selected = [dish_map[uid] for uid in shortlist_uids if uid in dish_map]

    if not selected:
        return True, [], empty_summary, empty_fig, empty_fig, empty_fig

    plan, result = app_ctx.planning.create_plan(
        name="Generated Plan",
        dishes=selected,
        weeks=4,
        dishes_per_week=4,
    )

    # Collect data for analysis
    week_cards = []
    category_data = []
    all_categories_used = set()
    cuisine_counts = Counter()
    region_counts = Counter()

    for i, week in enumerate(plan.weeks, 1):
        dish_names = [dish_map[uid].name for uid in week.dishes if uid in dish_map]

        # Build card for this week
        week_cards.append(
            dmc.Card(
                [
                    dmc.Text(f"Week {i}", fw=700, size="sm"),
                    dmc.Divider(my="xs"),
                    dmc.Stack(
                        [dmc.Text(name, size="sm", c="dark", inherit=False) for name in dish_names]
                        if dish_names
                        else [dmc.Text("Empty", c="dimmed", size="sm")],
                        gap="xs",
                    ),
                ],
                withBorder=True,
                p="sm",
            )
        )

        # Collect data for charts
        week_categories = Counter()
        for uid in week.dishes:
            if uid in dish_map:
                dish = dish_map[uid]
                # Categories
                for cat in dish.categories:
                    week_categories[cat.value] += 1
                    all_categories_used.add(cat.value)
                # Cuisine and region
                cuisine_counts[dish.cuisine.value.title()] += 1
                region_counts[dish.region.value.title()] += 1

        for cat, count in week_categories.items():
            category_data.append({
                "week": f"Week {i}",
                "category": cat,
                "count": count,
            })

    # Chart 1: Categories by Week (stacked bar)
    if category_data:
        category_fig = px.bar(
            category_data,
            x="week",
            y="count",
            color="category",
            title="Categories by Week",
            barmode="stack",
        )
        category_fig.update_layout(
            xaxis_title="",
            yaxis_title="Count",
            legend_title="Category",
            margin=dict(t=50, b=40, l=50, r=20),
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        )
    else:
        category_fig = empty_fig

    # Chart 2: Cuisine Distribution (pie)
    if cuisine_counts:
        cuisine_fig = px.pie(
            values=list(cuisine_counts.values()),
            names=list(cuisine_counts.keys()),
            title="Cuisine Variety",
            hole=0.4,  # Donut style
        )
        cuisine_fig.update_layout(
            margin=dict(t=50, b=40, l=20, r=20),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
            showlegend=True,
        )
        cuisine_fig.update_traces(textposition='inside', textinfo='percent')
    else:
        cuisine_fig = empty_fig

    # Chart 3: Region Balance (pie)
    if region_counts:
        region_fig = px.pie(
            values=list(region_counts.values()),
            names=list(region_counts.keys()),
            title="Region Balance",
            color_discrete_map={"Eastern": "#228be6", "Western": "#fd7e14"},
        )
        region_fig.update_layout(
            margin=dict(t=50, b=40, l=20, r=20),
            legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        )
        region_fig.update_traces(textposition='inside', textinfo='percent+label')
    else:
        region_fig = empty_fig

    # Score Summary
    total_categories = len(Category)
    categories_covered = len(all_categories_used)
    cat_score = round((categories_covered / total_categories) * 100)
    unique_cuisines = len(cuisine_counts)
    eastern_pct = round(region_counts.get("Eastern", 0) / sum(region_counts.values()) * 100) if region_counts else 0
    western_pct = 100 - eastern_pct

    # Horizontal score summary with key metrics
    score_summary = [
        dmc.Badge(f"Diversity: {cat_score}%", size="lg", color="blue", variant="filled"),
        dmc.Badge(f"Categories: {categories_covered}/{total_categories}", size="lg", variant="light"),
        dmc.Badge(f"Cuisines: {unique_cuisines}", size="lg", variant="light"),
        dmc.Badge(f"Balance: {eastern_pct}% E / {western_pct}% W", size="lg", variant="light"),
    ]

    return (
        True,  # Open modal
        week_cards,
        score_summary,
        category_fig,
        cuisine_fig,
        region_fig,
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
    prevent_initial_call=True,
)
def open_modal(add_clicks, edit_clicks, is_open):
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
            app_ctx = get_app_context()
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
    prevent_initial_call=True,
)
def save_dish(n_clicks, mode, uid, name, cuisine, categories, tags, recipe, shortlist):
    """Save dish (add new or update existing)."""
    if not name or not cuisine:
        # Don't close modal if required fields missing
        return True, shortlist

    app_ctx = get_app_context()

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
    prevent_initial_call=True,
)
def delete_dish(n_clicks, uid, shortlist):
    """Delete dish from catalogue."""
    if not uid:
        return True, shortlist

    app_ctx = get_app_context()
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
