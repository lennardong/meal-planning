"""Meal Planning CLI.

Command-line interface for meal planning operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from meal_planning.app.bootstrap import create_app
from meal_planning.catalogue.domain.models import VOIngredient, VODish
from meal_planning.catalogue.domain.enums import PurchaseType, IngredientTag, DishTag
from meal_planning.planning.domain.enums import Day
from meal_planning.ai.domain.context import VOAIContext

app = typer.Typer(
    name="meal-plan",
    help="AI-powered meal planning CLI",
    no_args_is_help=True,
)
console = Console()

# Default data path
DATA_PATH = Path("data/meals.json")


# ============ Catalogue Commands ============


@app.command()
def add_ingredient(
    name: str = typer.Argument(..., help="Ingredient name"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Category tag"),
    bulk: bool = typer.Option(False, "--bulk", "-b", help="Mark as bulk purchase"),
):
    """Add a new ingredient to the catalogue."""
    with create_app(DATA_PATH) as ctx:
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

        result = ctx.store.ingredients.add(ingredient)
        if result.is_ok():
            console.print(f"[green]Added ingredient: {name} ({ingredient.uid})[/green]")
        else:
            console.print(f"[red]Error: {result.error}[/red]")
            raise typer.Exit(1)


@app.command()
def add_dish(
    name: str = typer.Argument(..., help="Dish name"),
    tag: Optional[str] = typer.Option(None, "--tag", "-t", help="Style tag (Eastern/Western)"),
    ingredients: Optional[str] = typer.Option(None, "--ingredients", "-i", help="Comma-separated ingredient names"),
):
    """Add a new dish to the catalogue."""
    with create_app(DATA_PATH) as ctx:
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
                result = ctx.store.ingredients.get_by_name(ing_name)
                if result.is_ok():
                    ingredient_uids.append(result.unwrap().uid)
                else:
                    console.print(f"[yellow]Warning: Ingredient '{ing_name}' not found[/yellow]")

        dish = VODish(
            name=name,
            tags=tags,
            ingredient_uids=tuple(ingredient_uids),
        )

        result = ctx.store.dishes.add(dish)
        if result.is_ok():
            console.print(f"[green]Added dish: {name} ({dish.uid})[/green]")
        else:
            console.print(f"[red]Error: {result.error}[/red]")
            raise typer.Exit(1)


@app.command()
def list_ingredients():
    """List all ingredients in the catalogue."""
    with create_app(DATA_PATH) as ctx:
        ingredients = ctx.store.ingredients.list_all()

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


@app.command()
def list_dishes():
    """List all dishes in the catalogue."""
    with create_app(DATA_PATH) as ctx:
        dishes = ctx.store.dishes.list_all()

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
                result = ctx.store.ingredients.get(uid)
                if result.is_ok():
                    ing_names.append(result.unwrap().name)

            table.add_row(
                dish.uid,
                dish.name,
                ", ".join(t.value for t in dish.tags),
                ", ".join(ing_names) if ing_names else "(none)",
            )

        console.print(table)


# ============ Planning Commands ============


@app.command()
def show(
    month: str = typer.Argument(..., help="Month in format YYYY-MM (e.g., 2025-01)"),
):
    """Show the meal plan for a month."""
    with create_app(DATA_PATH) as ctx:
        summary = ctx.agent.get_plan_summary(month)
        console.print(summary)


@app.command()
def schedule(
    month: str = typer.Argument(..., help="Month in format YYYY-MM"),
    week: int = typer.Option(..., "--week", "-w", help="Week number (1-4)"),
    day: str = typer.Option(..., "--day", "-d", help="Day (Mon, Tue, etc.)"),
    dish: Optional[str] = typer.Option(None, "--dish", help="Dish name (omit to clear)"),
):
    """Schedule a dish for a specific day."""
    with create_app(DATA_PATH) as ctx:
        # Validate week
        if not 1 <= week <= 4:
            console.print("[red]Week must be 1-4[/red]")
            raise typer.Exit(1)

        # Parse day
        try:
            day_enum = Day(day)
        except ValueError:
            console.print(f"[red]Invalid day: {day}[/red]")
            console.print(f"Valid days: {[d.value for d in Day]}")
            raise typer.Exit(1)

        # Find dish UID
        dish_uid = None
        if dish:
            result = ctx.store.dishes.get_by_name(dish)
            if result.is_err():
                console.print(f"[red]Dish not found: {dish}[/red]")
                raise typer.Exit(1)
            dish_uid = result.unwrap().uid

        # Schedule
        ctx.agent.schedule_dish(month, week, day_enum, dish_uid)

        if dish_uid:
            console.print(f"[green]Scheduled '{dish}' for {day} Week {week}[/green]")
        else:
            console.print(f"[green]Cleared {day} Week {week}[/green]")


@app.command()
def shopping(
    month: str = typer.Argument(..., help="Month in format YYYY-MM"),
    week: int = typer.Option(..., "--week", "-w", help="Week number (1-4)"),
):
    """Generate shopping list for a week."""
    with create_app(DATA_PATH) as ctx:
        shopping_list = ctx.agent.generate_shopping_list(month, week)

        console.print(f"\n[bold]Shopping List for {month} Week {week}[/bold]\n")

        if shopping_list.bulk:
            console.print("[bold cyan]Bulk Items (Monthly Purchase):[/bold cyan]")
            for ing in shopping_list.bulk:
                console.print(f"  - {ing.name}")

        if shopping_list.weekly:
            console.print("\n[bold green]Weekly Items (Fresh Purchase):[/bold green]")
            for ing in shopping_list.weekly:
                console.print(f"  - {ing.name}")

        if not shopping_list.bulk and not shopping_list.weekly:
            console.print("[yellow]No items scheduled for this week[/yellow]")


@app.command()
def variety(
    month: str = typer.Argument(..., help="Month in format YYYY-MM"),
):
    """Analyze variety in a month's meal plan."""
    with create_app(DATA_PATH) as ctx:
        report = ctx.agent.assess_variety(month)

        console.print(f"\n[bold]Variety Report for {month}[/bold]\n")
        console.print(f"Variety Score: [bold]{report.variety_score}/100[/bold]")
        console.print(f"Unique Dishes: {report.unique_dish_count}")
        console.print(f"Total Scheduled: {report.total_scheduled_count}")

        if report.tag_distribution:
            console.print("\n[bold]Tag Distribution:[/bold]")
            for tag, count in report.tag_distribution.items():
                console.print(f"  {tag}: {count}")

        if report.repeated_dishes:
            console.print("\n[bold yellow]Repeated Dishes (>2 times):[/bold yellow]")
            for uid, count in report.repeated_dishes.items():
                result = ctx.store.dishes.get(uid)
                name = result.unwrap().name if result.is_ok() else uid
                console.print(f"  {name}: {count} times")


# ============ Context Commands ============


@app.command()
def add_context(
    context: str = typer.Argument(..., help="Context description"),
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Category (dietary, location, etc.)"),
):
    """Add an AI context (user preference/constraint)."""
    with create_app(DATA_PATH) as ctx:
        ai_context = VOAIContext(
            context=context,
            category=category,
        )

        result = ctx.store.ai_contexts.add(ai_context)
        if result.is_ok():
            console.print(f"[green]Added context: {ai_context.uid}[/green]")
        else:
            console.print(f"[red]Error: {result.error}[/red]")
            raise typer.Exit(1)


@app.command()
def list_contexts():
    """List all AI contexts (user preferences)."""
    with create_app(DATA_PATH) as ctx:
        contexts = ctx.store.ai_contexts.list_all()

        if not contexts:
            console.print("[yellow]No contexts configured[/yellow]")
            return

        table = Table(title="AI Contexts")
        table.add_column("UID", style="dim")
        table.add_column("Category")
        table.add_column("Context")

        for context in contexts:
            table.add_row(
                context.uid,
                context.category or "(none)",
                context.context[:50] + "..." if len(context.context) > 50 else context.context,
            )

        console.print(table)


# ============ Seed Commands ============


@app.command()
def seed():
    """Seed the database with sample data."""
    with create_app(DATA_PATH) as ctx:
        # Add ingredients
        rice = VOIngredient(name="Rice", tags=(IngredientTag.GRAIN,), purchase_type=PurchaseType.BULK)
        potato = VOIngredient(name="Potato", tags=(IngredientTag.VEGETABLE,), purchase_type=PurchaseType.BULK)
        spinach = VOIngredient(name="Spinach", tags=(IngredientTag.VEGETABLE,), purchase_type=PurchaseType.WEEKLY)
        eggs = VOIngredient(name="Eggs", tags=(IngredientTag.PROTEIN,), purchase_type=PurchaseType.WEEKLY)
        kimchi = VOIngredient(name="Kimchi", tags=(IngredientTag.VEGETABLE,), purchase_type=PurchaseType.WEEKLY)

        for ing in [rice, potato, spinach, eggs, kimchi]:
            ctx.store.ingredients.add(ing)
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
            ctx.store.dishes.add(dish)
        console.print("[green]Added 3 sample dishes[/green]")

        # Add contexts
        vegetarian = VOAIContext(
            category="dietary",
            context="We are vegetarian. We do not eat any meat, but do eat dairy and eggs.",
        )
        location = VOAIContext(
            category="location",
            context="We live in Johor Bahru, Malaysia. We prefer local ingredients.",
        )

        for context in [vegetarian, location]:
            ctx.store.ai_contexts.add(context)
        console.print("[green]Added 2 sample contexts[/green]")

        console.print("\n[bold green]Seed complete![/bold green]")


if __name__ == "__main__":
    app()
