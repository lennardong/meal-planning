"""Configuration module."""

from meal_planning.infra.config.settings import (
    DEFAULT_DATA_PATH,
    DEFAULT_USER_ID,
    DEFAULT_AI_MODEL,
    get_data_path,
    get_user_id,
)

__all__ = [
    "DEFAULT_DATA_PATH",
    "DEFAULT_USER_ID",
    "DEFAULT_AI_MODEL",
    "get_data_path",
    "get_user_id",
]
