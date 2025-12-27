"""Catalogue CLI commands.

Commands for managing dishes and their categories.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from meal_planning.core.catalogue.models import Dish
from meal_planning.core.catalogue.enums import Category, Cuisine

app = typer.Typer(
    name="catalogue",
    help="Manage dishes and categories",
    no_args_is_help=True,
)
console = Console()


def get_services():
    """Get services from app context."""
    from meal_planning.app import get_app_context

    return get_app_context()


@app.command("add-dish")
def add_dish(
    name: str = typer.Argument(..., help="Dish name"),
    categories: str = typer.Option(
        ..., "--categories", "-c", help="Comma-separated categories (e.g. grains,greens,fermented)"
    ),
    cuisine: str = typer.Option(
        ..., "--cuisine", help="Cuisine type (e.g. korean, thai, italian)"
    ),
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t", help="Optional custom tag"
    ),
    recipe: Optional[str] = typer.Option(
        None, "--recipe", "-r", help="Recipe reference (URL or notes)"
    ),
):
    """Add a new dish to the catalogue."""
    ctx = get_services()

    # Tags are open strings (auto-normalized)
    tags = (tag,) if tag else ()

    # Parse cuisine
    try:
        cuisine_enum = Cuisine(cuisine.strip().lower())
    except ValueError:
        console.print(f"[red]Invalid cuisine: {cuisine}[/red]")
        console.print(f"Valid cuisines: {[c.value for c in Cuisine]}")
        raise typer.Exit(1)

    # Parse categories
    category_list = []
    for cat_str in categories.split(","):
        cat_str = cat_str.strip().lower()
        try:
            category_list.append(Category(cat_str))
        except ValueError:
            console.print(f"[red]Invalid category: {cat_str}[/red]")
            console.print(f"Valid categories: {[c.value for c in Category]}")
            raise typer.Exit(1)

    dish = Dish(
        name=name,
        categories=tuple(category_list),
        cuisine=cuisine_enum,
        tags=tags,
        recipe_reference=recipe or "",
    )

    result = ctx.catalogue.add_dish(dish)
    if result.is_ok():
        ctx.catalogue.save()
        console.print(f"[green]Added dish: {dish.name} ({dish.uid})[/green]")
        console.print(f"  Cuisine: {dish.cuisine.value} ({dish.region.value})")
        console.print(f"  Categories: {', '.join(c.value for c in dish.categories)}")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_dishes():
    """List all dishes in the catalogue."""
    ctx = get_services()
    dishes = ctx.catalogue.list_dishes()

    if not dishes:
        console.print("[yellow]No dishes in catalogue[/yellow]")
        return

    table = Table(title="Dishes")
    table.add_column("UID", style="dim")
    table.add_column("Name")
    table.add_column("Cuisine")
    table.add_column("Region")
    table.add_column("Categories")
    table.add_column("Recipe")

    for dish in dishes:
        table.add_row(
            dish.uid,
            dish.name,
            dish.cuisine.value,
            dish.region.value,
            ", ".join(c.value for c in dish.categories) if dish.categories else "(none)",
            dish.recipe_reference[:30] + "..." if len(dish.recipe_reference) > 30 else dish.recipe_reference,
        )

    console.print(table)


@app.command("categories")
def list_categories():
    """List all available food categories."""
    from meal_planning.core.catalogue.enums import CATEGORY_PURCHASE_TYPE, PurchaseType

    table = Table(title="Food Categories")
    table.add_column("Category")
    table.add_column("Purchase Type")

    for cat in Category:
        purchase = CATEGORY_PURCHASE_TYPE.get(cat, PurchaseType.WEEKLY)
        table.add_row(cat.value, purchase.value)

    console.print(table)


@app.command("cuisines")
def list_cuisines():
    """List all available cuisine types."""
    from meal_planning.core.catalogue.enums import CUISINE_REGION, Region

    table = Table(title="Cuisine Types")
    table.add_column("Cuisine")
    table.add_column("Region")

    for cuisine in Cuisine:
        region = CUISINE_REGION.get(cuisine, Region.EASTERN)
        table.add_row(cuisine.value, region.value)

    console.print(table)


@app.command("delete")
def delete_dish(
    uid: str = typer.Argument(..., help="Dish UID to delete"),
):
    """Delete a dish from the catalogue."""
    ctx = get_services()

    result = ctx.catalogue.delete_dish(uid)
    if result.is_ok():
        ctx.catalogue.save()
        console.print(f"[green]Deleted dish: {uid}[/green]")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)
