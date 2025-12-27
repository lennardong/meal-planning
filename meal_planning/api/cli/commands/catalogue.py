"""Catalogue CLI commands.

Commands for managing ingredients and dishes.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from meal_planning.core.catalogue.models import VOIngredient, VODish
from meal_planning.core.catalogue.enums import PurchaseType, IngredientTag, DishTag

app = typer.Typer(
    name="catalogue",
    help="Manage ingredients and dishes",
    no_args_is_help=True,
)
console = Console()


def get_services():
    """Get services from app context."""
    from meal_planning.app import get_app_context

    return get_app_context()


@app.command("add-ingredient")
def add_ingredient(
    name: str = typer.Argument(..., help="Ingredient name"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Category tag"),
    bulk: bool = typer.Option(False, "--bulk", "-b", help="Mark as bulk purchase"),
):
    """Add a new ingredient to the catalogue."""
    ctx = get_services()

    # Parse tag
    tags = ()
    if tag:
        try:
            tags = (IngredientTag(tag),)
        except ValueError:
            console.print(f"[red]Invalid tag: {tag}[/red]")
            console.print(f"Valid tags: {[t.value for t in IngredientTag]}")
            raise typer.Exit(1)

    purchase_type = PurchaseType.BULK if bulk else PurchaseType.WEEKLY

    ingredient = VOIngredient(
        name=name,
        tags=tags,
        purchase_type=purchase_type,
    )

    result = ctx.catalogue.add_ingredient(ingredient)
    if result.is_ok():
        ctx.catalogue.save()
        console.print(f"[green]Added ingredient: {name} ({ingredient.uid})[/green]")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


@app.command("add-dish")
def add_dish(
    name: str = typer.Argument(..., help="Dish name"),
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t", help="Style tag (Eastern/Western)"
    ),
    ingredients: Optional[str] = typer.Option(
        None, "--ingredients", "-i", help="Comma-separated ingredient names"
    ),
):
    """Add a new dish to the catalogue."""
    ctx = get_services()

    # Parse tag
    tags = ()
    if tag:
        try:
            tags = (DishTag(tag),)
        except ValueError:
            console.print(f"[red]Invalid tag: {tag}[/red]")
            console.print(f"Valid tags: {[t.value for t in DishTag]}")
            raise typer.Exit(1)

    # Find ingredient UIDs
    ingredient_uids = []
    if ingredients:
        for ing_name in ingredients.split(","):
            ing_name = ing_name.strip()
            # Search by name in all ingredients
            found = None
            for ing in ctx.catalogue.list_ingredients():
                if ing.name.lower() == ing_name.lower():
                    found = ing
                    break
            if found:
                ingredient_uids.append(found.uid)
            else:
                console.print(f"[yellow]Warning: Ingredient '{ing_name}' not found[/yellow]")

    dish = VODish(
        name=name,
        tags=tags,
        ingredient_uids=tuple(ingredient_uids),
    )

    result = ctx.catalogue.add_dish(dish)
    if result.is_ok():
        ctx.catalogue.save()
        console.print(f"[green]Added dish: {name} ({dish.uid})[/green]")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_items(
    item_type: str = typer.Argument(
        "all", help="What to list: 'ingredients', 'dishes', or 'all'"
    ),
):
    """List catalogue items."""
    ctx = get_services()

    if item_type in ("ingredients", "all"):
        _list_ingredients(ctx)

    if item_type in ("dishes", "all"):
        _list_dishes(ctx)


def _list_ingredients(ctx):
    """Display ingredients table."""
    ingredients = ctx.catalogue.list_ingredients()

    if not ingredients:
        console.print("[yellow]No ingredients in catalogue[/yellow]")
        return

    table = Table(title="Ingredients")
    table.add_column("UID", style="dim")
    table.add_column("Name")
    table.add_column("Tags")
    table.add_column("Purchase")

    for ing in ingredients:
        table.add_row(
            ing.uid,
            ing.name,
            ", ".join(t.value for t in ing.tags),
            ing.purchase_type.value,
        )

    console.print(table)


def _list_dishes(ctx):
    """Display dishes table."""
    dishes = ctx.catalogue.list_dishes()

    if not dishes:
        console.print("[yellow]No dishes in catalogue[/yellow]")
        return

    table = Table(title="Dishes")
    table.add_column("UID", style="dim")
    table.add_column("Name")
    table.add_column("Tags")
    table.add_column("Ingredients")

    for dish in dishes:
        ing_names = []
        for uid in dish.ingredient_uids:
            result = ctx.catalogue.get_ingredient(uid)
            if result.is_ok():
                ing_names.append(result.unwrap().name)

        table.add_row(
            dish.uid,
            dish.name,
            ", ".join(t.value for t in dish.tags),
            ", ".join(ing_names) if ing_names else "(none)",
        )

    console.print(table)
