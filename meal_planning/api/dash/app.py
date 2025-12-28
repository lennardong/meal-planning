"""Meal Planning Dash App with Kanban-style Mantine UI."""

from __future__ import annotations

import os

import dash_mantine_components as dmc
from dash import Dash, dcc, html
from dash_iconify import DashIconify

# Import callbacks to register them
from meal_planning.api.dash import callbacks as _  # noqa: F401
from meal_planning.api.dash.components import dish_column, dish_modal, results_modal, info_modal
from meal_planning.app import get_app_context
from meal_planning.copy import get_copy
from meal_planning.theme import generate_category_css_vars

# Get services (auto-initializes if needed)
ctx = get_app_context()

# Create Dash app
app = Dash(__name__, external_stylesheets=[dmc.styles.CHARTS])

# Custom index with Google Fonts and generated CSS variables
app.index_string = f"""
<!DOCTYPE html>
<html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=BBH+Hegarty&family=DM+Sans:wght@400;600;700;900&family=Inter:wght@400;500&family=Nunito:wght@500;600;700&display=swap" rel="stylesheet">
        <style>{generate_category_css_vars()}</style>
        {{%metas%}}
        <title>Palate</title>
        {{%favicon%}}
        {{%css%}}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>
"""

# Build layout - no navbar, two-column main
layout = dmc.AppShell(
    [
        # Header with title above, buttons below
        dmc.AppShellHeader(
            dmc.Stack(
                [
                    # Title row
                    dcc.Markdown(
                        get_copy("app_header"),
                        style={"textAlign": "center", "margin": 0},
                    ),
                    # Buttons row (centered)
                    dmc.Group(
                        [
                            html.Button(
                                "Get Started",
                                id="get-started-btn",
                                className="chiclet chiclet--link",
                            ),
                            html.Button(
                                "Why Palate?",
                                id="info-btn",
                                className="chiclet chiclet--link",
                            ),
                        ],
                        justify="center",
                        gap="sm",
                    ),
                ],
                gap=0,
                align="center",
                justify="center",
                h="100%",
            ),
        ),
        # Main content - two columns + results
        dmc.AppShellMain(
            dmc.Stack(
                [
                    # Stores for state
                    dcc.Store(id="shortlist-store", data=[]),
                    dcc.Store(id="dish-modal-mode", data="add"),  # "add" or "edit"
                    dcc.Store(id="dish-modal-uid", data=None),  # uid being edited
                    # Modals
                    dish_modal(),
                    results_modal(),
                    info_modal("info-modal", "Why Palate?", "app_about"),
                    info_modal("get-started-modal", "Get Started", "app_get_started"),
                    # Row 1: Your Palette and Your Canvas columns
                    dmc.SimpleGrid(
                        [
                            dish_column("Your Palette", "catalogue", "right"),
                            dish_column("Your Canvas", "shortlist", "left"),
                        ],
                        cols={"base": 1, "md": 2},
                        spacing="md",
                    ),
                    # See Your Colors button (centered, rainbow gradient)
                    dmc.Center(
                        html.Button(
                            [
                                DashIconify(
                                    icon="mdi:palette",
                                    width=18,
                                    style={"marginRight": "8px"},
                                ),
                                "See Your Colors",
                            ],
                            id="generate-btn",
                            className="chiclet chiclet--action",
                        ),
                        py="md",
                    ),
                ],
                gap="md",
                p="md",
            )
        ),
    ],
    header={"height": 100},
    padding="md",
    id="appshell",
)

app.layout = dmc.MantineProvider(
    layout,
    theme={
        "primaryColor": "saffron",
        "colors": {
            "saffron": [
                "#FFF8E1",
                "#FFECB3",
                "#FFE082",
                "#FFD54F",
                "#FFCA28",
                "#F4A940",
                "#E09830",
                "#C68400",
                "#A66D00",
                "#8B5A00",
            ],
        },
        "defaultRadius": "md",
        # Typography handled by style.css (single source of truth)
    },
)


# WSGI entry point for gunicorn
server = app.server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=True, port=port)
