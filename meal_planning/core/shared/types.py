"""Functional types for error handling.

This module provides Result types following the Rust/functional programming pattern
for explicit error handling without exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, NoReturn

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


@dataclass(frozen=True, slots=True)
class Ok(Generic[T]):
    """Success result containing a value."""

    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        """Get the value. Always succeeds for Ok."""
        return self.value

    def unwrap_or(self, default: T) -> T:
        """Get the value or return default."""
        return self.value

    def map(self, fn: Callable[[T], U]) -> Ok[U]:
        """Apply function to value, returning new Ok."""
        return Ok(fn(self.value))

    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """Chain operations that might fail."""
        return fn(self.value)


@dataclass(frozen=True, slots=True)
class Err(Generic[E]):
    """Error result containing an error."""

    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> NoReturn:
        """Raises ValueError. Use unwrap_or for safe access."""
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_or(self, default: T) -> T:
        """Return the default value since this is an error."""
        return default

    def map(self, fn: Callable[[T], U]) -> "Err[E]":
        """No-op for Err, returns self."""
        return self

    def and_then(self, fn: Callable[[T], "Result[U, E]"]) -> "Err[E]":
        """No-op for Err, returns self."""
        return self


# Type alias for Result
Result = Ok[T] | Err[E]


# Domain Errors


@dataclass(frozen=True, slots=True)
class NotFoundError:
    """Entity not found in repository."""

    entity: str
    uid: str

    def __str__(self) -> str:
        return f"{self.entity} with uid '{self.uid}' not found"


@dataclass(frozen=True, slots=True)
class DuplicateError:
    """Entity with same uid already exists."""

    entity: str
    uid: str

    def __str__(self) -> str:
        return f"{self.entity} with uid '{self.uid}' already exists"


@dataclass(frozen=True, slots=True)
class ValidationError:
    """Domain validation failed."""

    message: str

    def __str__(self) -> str:
        return self.message
