"""Meal Planning CLI.

Command-line interface for meal planning operations.
Uses nested subcommands organized by domain.
"""

from __future__ import annotations

import typer
from rich.console import Console

from meal_planning.api.cli.commands import catalogue, planning, shopping, analysis, context
from meal_planning.core.catalogue.models import VOIngredient, VODish
from meal_planning.core.catalogue.enums import PurchaseType, IngredientTag, DishTag
from meal_planning.core.context.models import VOUserContext

app = typer.Typer(
    name="meal",
    help="AI-powered meal planning CLI",
    no_args_is_help=True,
)
console = Console()

# Register subcommand groups
app.add_typer(catalogue.app, name="catalogue")
app.add_typer(planning.app, name="plan")
app.add_typer(shopping.app, name="shop")
app.add_typer(analysis.app, name="analysis")
app.add_typer(context.app, name="context")


@app.command()
def seed():
    """Seed the database with sample data."""
    from meal_planning.app import get_app_context

    ctx = get_app_context()

    # Add ingredients
    rice = VOIngredient(
        name="Rice", tags=(IngredientTag.GRAIN,), purchase_type=PurchaseType.BULK
    )
    potato = VOIngredient(
        name="Potato", tags=(IngredientTag.VEGETABLE,), purchase_type=PurchaseType.BULK
    )
    spinach = VOIngredient(
        name="Spinach",
        tags=(IngredientTag.VEGETABLE,),
        purchase_type=PurchaseType.WEEKLY,
    )
    eggs = VOIngredient(
        name="Eggs", tags=(IngredientTag.PROTEIN,), purchase_type=PurchaseType.WEEKLY
    )
    kimchi = VOIngredient(
        name="Kimchi",
        tags=(IngredientTag.VEGETABLE,),
        purchase_type=PurchaseType.WEEKLY,
    )

    for ing in [rice, potato, spinach, eggs, kimchi]:
        ctx.catalogue.add_ingredient(ing)
    ctx.catalogue.save()
    console.print("[green]Added 5 sample ingredients[/green]")

    # Add dishes
    fried_rice = VODish(
        name="Kimchee Fried Rice",
        tags=(DishTag.EASTERN,),
        ingredient_uids=(rice.uid, kimchi.uid, eggs.uid),
    )
    shepherds_pie = VODish(
        name="Shepherd's Pie",
        tags=(DishTag.WESTERN,),
        ingredient_uids=(potato.uid,),
    )
    stir_fry = VODish(
        name="Vegetable Stir Fry",
        tags=(DishTag.EASTERN,),
        ingredient_uids=(spinach.uid,),
    )

    for dish in [fried_rice, shepherds_pie, stir_fry]:
        ctx.catalogue.add_dish(dish)
    ctx.catalogue.save()
    console.print("[green]Added 3 sample dishes[/green]")

    # Add contexts
    vegetarian = VOUserContext(
        category="dietary",
        context="We are vegetarian. We do not eat any meat, but do eat dairy and eggs.",
    )
    location = VOUserContext(
        category="location",
        context="We live in Johor Bahru, Malaysia. We prefer local ingredients.",
    )

    for user_context in [vegetarian, location]:
        ctx.context.add_context(user_context)
    ctx.context.save()
    console.print("[green]Added 2 sample contexts[/green]")

    console.print("\n[bold green]Seed complete![/bold green]")


@app.command()
def migrate():
    """Migrate data from old format to new format."""
    from meal_planning.infra.stores.migration import migrate_if_needed, check_migration_status
    from meal_planning.infra.config import get_data_path, get_user_id

    data_path = get_data_path()
    user_id = get_user_id()

    status = check_migration_status(data_path, user_id)

    if status["new_format_exists"]:
        console.print("[green]Data is already in new format[/green]")
        return

    if not status["old_format_exists"]:
        console.print("[yellow]No data to migrate[/yellow]")
        return

    console.print("Migrating data to new format...")
    if migrate_if_needed(data_path, user_id):
        console.print("[green]Migration complete![/green]")
    else:
        console.print("[red]Migration failed[/red]")


@app.command()
def status():
    """Show data status and storage info."""
    from meal_planning.infra.stores.migration import check_migration_status
    from meal_planning.infra.config import get_data_path, get_user_id

    data_path = get_data_path()
    user_id = get_user_id()

    console.print(f"[bold]Data Status[/bold]")
    console.print(f"  Data path: {data_path}")
    console.print(f"  User ID: {user_id}")

    status = check_migration_status(data_path, user_id)
    console.print(f"  Old format exists: {status['old_format_exists']}")
    console.print(f"  New format exists: {status['new_format_exists']}")
    console.print(f"  Needs migration: {status['needs_migration']}")


def main():
    """Entry point for the CLI."""
    # Initialize app context before running commands
    from meal_planning.app import initialize_app

    initialize_app()
    app()


if __name__ == "__main__":
    main()
