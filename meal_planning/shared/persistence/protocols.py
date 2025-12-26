"""Base repository protocols.

This module defines abstract repository interfaces following the Repository pattern
from Cosmic Python. Concrete implementations can use JSON, TinyDB, MongoDB, etc.
"""

from __future__ import annotations

from typing import Protocol, TypeVar, Sequence, runtime_checkable

from meal_planning.shared.types import Result, NotFoundError, DuplicateError

T = TypeVar("T")


@runtime_checkable
class Repository(Protocol[T]):
    """Base repository protocol for CRUD operations.

    All methods return Result types for explicit error handling.
    Implementations should be swappable (JSON, TinyDB, Mongo, etc.).
    """

    def add(self, entity: T) -> Result[T, DuplicateError]:
        """Add a new entity.

        Args:
            entity: Entity to add.

        Returns:
            Ok(entity) on success, Err(DuplicateError) if uid exists.
        """
        ...

    def get(self, uid: str) -> Result[T, NotFoundError]:
        """Get entity by uid.

        Args:
            uid: Unique identifier.

        Returns:
            Ok(entity) if found, Err(NotFoundError) otherwise.
        """
        ...

    def list_all(self) -> Sequence[T]:
        """List all entities.

        Returns:
            Sequence of all entities (may be empty).
        """
        ...

    def update(self, entity: T) -> Result[T, NotFoundError]:
        """Update an existing entity.

        Args:
            entity: Entity with updated values (uid must exist).

        Returns:
            Ok(entity) on success, Err(NotFoundError) if uid not found.
        """
        ...

    def delete(self, uid: str) -> Result[None, NotFoundError]:
        """Delete entity by uid.

        Args:
            uid: Unique identifier of entity to delete.

        Returns:
            Ok(None) on success, Err(NotFoundError) if not found.
        """
        ...
