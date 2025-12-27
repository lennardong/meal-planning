"""Shared types across bounded contexts."""

from meal_planning.core.shared.types import (
    Ok,
    Err,
    Result,
    NotFoundError,
    DuplicateError,
    ValidationError,
)

__all__ = [
    "Ok",
    "Err",
    "Result",
    "NotFoundError",
    "DuplicateError",
    "ValidationError",
]
