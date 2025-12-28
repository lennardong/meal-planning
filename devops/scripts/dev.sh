#!/bin/bash
# Dev script to run Dash frontend with hot reloading
# Uses port 8051 to avoid conflict with Docker (8050)

cd "$(dirname "$0")/../.." || exit 1

export PORT=8051

echo "Starting Dash dev server with hot reloading..."
echo "Open http://127.0.0.1:${PORT} in your browser"
echo ""

uv run python -m meal_planning.api.dash.app
