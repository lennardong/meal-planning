"""Meal Planning Dash App with Kanban-style Mantine UI."""

from __future__ import annotations

import dash_mantine_components as dmc
from dash import Dash, dcc
from dash_iconify import DashIconify

# Import callbacks to register them
from meal_planning.api.dash import callbacks as _  # noqa: F401
from meal_planning.api.dash.components import dish_column, dish_modal, results_modal
from meal_planning.app import get_app_context
from meal_planning.copy import get_copy

# Get services (auto-initializes if needed)
ctx = get_app_context()

# Create Dash app
app = Dash(__name__, external_stylesheets=[dmc.styles.CHARTS])

# Custom index with Google Fonts
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
        {%metas%}
        <title>Palate</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

# Build layout - no navbar, two-column main
layout = dmc.AppShell(
    [
        # Header with title + info button
        dmc.AppShellHeader(
            dmc.Group(
                [
                    dcc.Markdown(
                        get_copy("app_header"),
                        style={"textAlign": "center", "margin": 0},
                    ),
                    dmc.Button(
                        "Why Palate?",
                        id="info-btn",
                        variant="subtle",
                        color="gray",
                        size="xs",
                        radius="xl",
                    ),
                ],
                justify="center",
                align="center",
                h="100%",
                gap="xs",
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
                    # Info modal (about content)
                    dmc.Modal(
                        id="info-modal",
                        title="Why Palate?",
                        centered=True,
                        size="lg",
                        children=dmc.ScrollArea(
                            dcc.Markdown(
                                get_copy("app_about"),
                                style={"fontSize": "14px", "lineHeight": "1.6"},
                            ),
                            h="60vh",
                        ),
                    ),
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
                        dmc.Button(
                            "See Your Colors",
                            id="generate-btn",
                            leftSection=DashIconify(icon="mdi:palette"),
                            size="md",
                            radius="xl",
                            styles={
                                "root": {
                                    "background": "linear-gradient(135deg, #F4A940 0%, #E8C547 25%, #5BA4A4 50%, #7B4B94 75%, #D46A84 100%)",
                                    "border": "none",
                                    "boxShadow": "0 2px 8px rgba(0,0,0,0.15)",
                                }
                            },
                        ),
                        py="md",
                    ),
                ],
                gap="md",
                p="md",
            )
        ),
    ],
    header={"height": 80},
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
        "fontFamily": "Inter, sans-serif",
        "headings": {"fontFamily": "DM Sans, sans-serif"},
        "defaultRadius": "md",
    },
)


# WSGI entry point for gunicorn
server = app.server

if __name__ == "__main__":
    app.run(debug=True)
