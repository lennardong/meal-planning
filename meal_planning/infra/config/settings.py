"""Application configuration settings."""

from __future__ import annotations

from pathlib import Path


# Default paths
DEFAULT_DATA_PATH = Path("data")
DEFAULT_USER_ID = "default"

# AI settings
DEFAULT_AI_MODEL = "claude-3-haiku-20240307"


def get_data_path() -> Path:
    """Get the data storage path.

    Can be overridden via MEAL_PLANNING_DATA_PATH env var.
    """
    import os

    env_path = os.environ.get("MEAL_PLANNING_DATA_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DATA_PATH


def get_user_id() -> str:
    """Get the current user ID.

    Can be overridden via MEAL_PLANNING_USER_ID env var.
    """
    import os

    return os.environ.get("MEAL_PLANNING_USER_ID", DEFAULT_USER_ID)
