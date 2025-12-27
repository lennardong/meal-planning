"""Meal Planning Dash App with Kanban-style Mantine UI."""

from __future__ import annotations

from dash import Dash, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from meal_planning.app import get_app_context
from meal_planning.api.dash.components import (
    dish_column,
    results_modal,
    dish_modal,
)

# Import callbacks to register them
from meal_planning.api.dash import callbacks as _  # noqa: F401

# Get services (auto-initializes if needed)
ctx = get_app_context()

# Create Dash app
app = Dash(__name__, external_stylesheets=[dmc.styles.CHARTS])

# Build layout - no navbar, two-column main
layout = dmc.AppShell(
    [
        # Header with centered title only
        dmc.AppShellHeader(
            dmc.Center(
                dmc.Title(
                    "Rewilding the Gut: A Monthly Meal Planner",
                    order=3,
                ),
                h="100%",
            )
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
                    # Row 1: Catalogue and Shortlist columns
                    dmc.SimpleGrid(
                        [
                            dish_column("Catalogue", "catalogue", "right"),
                            dish_column("Shortlist", "shortlist", "left"),
                        ],
                        cols={"base": 1, "md": 2},
                        spacing="md",
                    ),
                    # Generate Plan button (centered, not stretched)
                    dmc.Center(
                        dmc.Button(
                            "Generate Plan",
                            id="generate-btn",
                            leftSection=DashIconify(icon="mdi:flash"),
                            size="md",
                            radius="xl",
                            color="dark",
                        ),
                        py="md",
                    ),
                ],
                gap="lg",
                p="md",
            )
        ),
    ],
    header={"height": 60},
    padding="md",
    id="appshell",
)

app.layout = dmc.MantineProvider(
    layout,
    theme={
        "primaryColor": "dark",
        "defaultRadius": 0,
    },
)


if __name__ == "__main__":
    app.run(debug=True)
