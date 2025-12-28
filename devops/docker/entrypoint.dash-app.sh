#!/bin/bash
set -euo pipefail

readonly PORT="${PORT:-8060}"
readonly WORKERS="${WORKERS:-2}"
readonly APP_MODULE="meal_planning.api.dash.app:server"

exec .venv/bin/gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WORKERS}" \
    --access-logfile - \
    --error-logfile - \
    "${APP_MODULE}"
