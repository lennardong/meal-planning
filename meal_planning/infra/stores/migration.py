"""Data migration utilities.

Handles migration from old data formats to current format.
"""

from __future__ import annotations

import json
from pathlib import Path


def migrate_if_needed(data_path: Path, user_id: str = "default") -> bool:
    """Run any needed data migrations.

    Checks for old formats and migrates to current format if needed.
    Creates backups of original files before migration.

    Args:
        data_path: Base path for data storage.
        user_id: User identifier for new structure.

    Returns:
        True if any migration was performed, False otherwise.
    """
    migrated = False

    # Migration 1: Old monolithic meals.json to per-aggregate files
    if _migrate_meals_json(data_path, user_id):
        migrated = True

    # Migration 2: Old MonthlyPlan format to new MealPlan format
    if _migrate_plan_format(data_path, user_id):
        migrated = True

    return migrated


def _migrate_meals_json(data_path: Path, user_id: str) -> bool:
    """Migrate old meals.json to per-aggregate files.

    Old format: Single meals.json with all data
    New format: Separate files per aggregate (dishes.json, plans.json, etc.)
    """
    old_file = data_path / "meals.json"
    new_dir = data_path / user_id

    if not old_file.exists():
        return False

    if (new_dir / "dishes.json").exists():
        return False  # Already migrated

    try:
        old_data = json.loads(old_file.read_text())
    except (json.JSONDecodeError, OSError) as e:
        print(f"Warning: Could not read old format: {e}")
        return False

    new_dir.mkdir(parents=True, exist_ok=True)

    _write_json(new_dir / "dishes.json", old_data.get("dish_bank", {}))
    _write_json(new_dir / "plans.json", old_data.get("plans", {}))
    _write_json(new_dir / "contexts.json", old_data.get("ai_context_bank", {}))

    # Backup original
    backup_path = data_path / "meals.json.backup"
    old_file.rename(backup_path)
    print(f"Migration complete. Original backed up to: {backup_path}")

    return True


def _migrate_plan_format(data_path: Path, user_id: str) -> bool:
    """Migrate old MonthlyPlan format to new MealPlan format.

    Old format:
        {
            "PLAN-xxx": {
                "uid": "PLAN-xxx",
                "month": "2025-01",
                "weeks": [{"weekday_dinners": {...}, "weekend_meals": {...}}, ...]
            }
        }

    New format:
        {
            "PLAN-xxx": {
                "uid": "PLAN-xxx",
                "name": "January 2025",
                "weeks": [{"dishes": ["DISH-xxx", ...]}, ...]
            }
        }
    """
    plans_file = data_path / user_id / "plans.json"

    if not plans_file.exists():
        return False

    try:
        plans_data = json.loads(plans_file.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    if not plans_data:
        return False

    # Check if any plans need migration
    needs_migration = any(
        "month" in plan and "name" not in plan
        for plan in plans_data.values()
    )

    if not needs_migration:
        return False

    # Backup original
    backup_path = plans_file.with_suffix(".json.old")
    plans_file.rename(backup_path)

    # Migrate each plan
    migrated_plans = {}
    for uid, plan in plans_data.items():
        if "month" in plan and "name" not in plan:
            migrated_plans[uid] = _convert_monthly_plan(plan)
        else:
            migrated_plans[uid] = plan

    _write_json(plans_file, migrated_plans)
    print(f"Plan format migration complete. Original backed up to: {backup_path}")

    return True


def _convert_monthly_plan(old_plan: dict) -> dict:
    """Convert old MonthlyPlan to new MealPlan format."""
    # Convert month "2025-01" to name "January 2025"
    month_str = old_plan.get("month", "Unknown")
    try:
        year, month = month_str.split("-")
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        name = f"{month_names[int(month) - 1]} {year}"
    except (ValueError, IndexError):
        name = month_str

    # Convert weeks
    new_weeks = []
    for old_week in old_plan.get("weeks", []):
        dishes = []
        # Extract dish UIDs from weekday_dinners
        for dish_uid in old_week.get("weekday_dinners", {}).values():
            if dish_uid is not None:
                dishes.append(dish_uid)
        # Extract dish UIDs from weekend_meals
        for dish_uid in old_week.get("weekend_meals", {}).values():
            if dish_uid is not None:
                dishes.append(dish_uid)
        new_weeks.append({"dishes": tuple(dishes)})

    return {
        "uid": old_plan.get("uid", ""),
        "name": name,
        "weeks": tuple(new_weeks),
    }


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
        "new_format_exists": (new_dir / "dishes.json").exists(),
        "backup_exists": (data_path / "meals.json.backup").exists(),
        "needs_migration": old_file.exists() and not (new_dir / "dishes.json").exists(),
    }
