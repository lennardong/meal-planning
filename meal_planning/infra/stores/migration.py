"""Data migration utilities.

Handles migration from old single-file format to new per-aggregate format.
"""

from __future__ import annotations

import json
from pathlib import Path


def migrate_if_needed(data_path: Path, user_id: str = "default") -> bool:
    """Migrate old meals.json to per-aggregate files.

    Checks for old format and migrates to new format if needed.
    Creates a backup of the original file.

    Args:
        data_path: Base path for data storage.
        user_id: User identifier for new structure.

    Returns:
        True if migration was performed, False otherwise.
    """
    old_file = data_path / "meals.json"
    new_dir = data_path / user_id

    # Check if migration is needed
    if not old_file.exists():
        return False  # Nothing to migrate

    if (new_dir / "ingredients.json").exists():
        return False  # Already migrated

    # Load old format
    try:
        old_data = json.loads(old_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not read old format: {e}")
        return False

    # Create new directory
    new_dir.mkdir(parents=True, exist_ok=True)

    # Split and write per-aggregate files
    _write_json(
        new_dir / "ingredients.json",
        old_data.get("ingredient_bank", {}),
    )
    _write_json(
        new_dir / "dishes.json",
        old_data.get("dish_bank", {}),
    )
    _write_json(
        new_dir / "plans.json",
        old_data.get("plans", {}),
    )
    _write_json(
        new_dir / "contexts.json",
        old_data.get("ai_context_bank", {}),
    )

    # Backup original
    backup_path = data_path / "meals.json.backup"
    old_file.rename(backup_path)
    print(f"Migration complete. Original backed up to: {backup_path}")

    return True


def _write_json(path: Path, data: dict) -> None:
    """Write JSON data to file atomically."""
    tmp = path.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def check_migration_status(data_path: Path, user_id: str = "default") -> dict:
    """Check current data status.

    Args:
        data_path: Base path for data storage.
        user_id: User identifier.

    Returns:
        Status dict with information about data state.
    """
    old_file = data_path / "meals.json"
    new_dir = data_path / user_id

    return {
        "old_format_exists": old_file.exists(),
        "new_format_exists": (new_dir / "ingredients.json").exists(),
        "backup_exists": (data_path / "meals.json.backup").exists(),
        "needs_migration": old_file.exists()
        and not (new_dir / "ingredients.json").exists(),
    }
