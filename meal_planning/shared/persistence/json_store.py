"""JSON file persistence layer.

This module provides a simple JSON file store that loads data into memory
and saves on explicit save() call.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class JsonStore:
    """JSON file store with in-memory data access.

    Loads entire JSON file into memory on initialization.
    Modifications happen in-memory, persisted on save().
    """

    def __init__(self, path: Path) -> None:
        """Initialize store with file path.

        Args:
            path: Path to JSON file. Created with empty structure if not exists.
        """
        self._path = path
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        """Load data from JSON file or create empty structure."""
        if self._path.exists():
            return json.loads(self._path.read_text(encoding="utf-8"))
        return self._empty_structure()

    def _empty_structure(self) -> dict[str, Any]:
        """Return empty data structure for new files."""
        return {
            "ingredient_bank": {},
            "dish_bank": {},
            "ai_context_bank": {},
            "plans": {},
        }

    def save(self) -> None:
        """Persist data to JSON file.

        Creates parent directories if they don't exist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    @property
    def ingredient_bank(self) -> dict[str, Any]:
        """Access ingredient bank data."""
        return self._data["ingredient_bank"]

    @property
    def dish_bank(self) -> dict[str, Any]:
        """Access dish bank data."""
        return self._data["dish_bank"]

    @property
    def ai_context_bank(self) -> dict[str, Any]:
        """Access AI context bank data."""
        return self._data["ai_context_bank"]

    @property
    def plans(self) -> dict[str, Any]:
        """Access plans data."""
        return self._data["plans"]

    def reload(self) -> None:
        """Reload data from file, discarding in-memory changes."""
        self._data = self._load()

    def clear(self) -> None:
        """Clear all data in memory (does not save)."""
        self._data = self._empty_structure()
