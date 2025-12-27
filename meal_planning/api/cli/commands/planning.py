"""Planning CLI commands.

Commands for managing shortlist and meal plans.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="plan",
    help="Manage shortlist and meal plans",
    no_args_is_help=True,
)
console = Console()

# Shortlist subcommand group
shortlist_app = typer.Typer(
    name="shortlist",
    help="Manage dish shortlist for planning",
    no_args_is_help=True,
)
app.add_typer(shortlist_app, name="shortlist")


def get_services():
    """Get services from app context."""
    from meal_planning.app import get_app_context

    return get_app_context()


# === Shortlist Commands ===


@shortlist_app.command("add")
def shortlist_add(
    dish: str = typer.Argument(..., help="Dish name or UID to add"),
):
    """Add a dish to the shortlist."""
    ctx = get_services()

    # Resolve dish by name or UID
    all_dishes = ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}
    name_map = {d.name.lower(): d for d in all_dishes}

    resolved = None
    if dish in dish_map:
        resolved = dish_map[dish]
    elif dish.lower() in name_map:
        resolved = name_map[dish.lower()]

    if not resolved:
        console.print(f"[red]Dish not found: {dish}[/red]")
        raise typer.Exit(1)

    shortlist = ctx.planning.add_to_shortlist(resolved.uid)
    console.print(f"[green]Added '{resolved.name}' to shortlist[/green]")
    console.print(f"Shortlist now has {len(shortlist)} dishes")


@shortlist_app.command("remove")
def shortlist_remove(
    dish: str = typer.Argument(..., help="Dish name or UID to remove"),
):
    """Remove a dish from the shortlist."""
    ctx = get_services()

    # Resolve dish by name or UID
    all_dishes = ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}
    name_map = {d.name.lower(): d for d in all_dishes}

    resolved = None
    if dish in dish_map:
        resolved = dish_map[dish]
    elif dish.lower() in name_map:
        resolved = name_map[dish.lower()]

    if not resolved:
        console.print(f"[red]Dish not found: {dish}[/red]")
        raise typer.Exit(1)

    shortlist = ctx.planning.remove_from_shortlist(resolved.uid)
    console.print(f"[green]Removed '{resolved.name}' from shortlist[/green]")
    console.print(f"Shortlist now has {len(shortlist)} dishes")


@shortlist_app.command("list")
def shortlist_list():
    """Show all dishes in the shortlist."""
    ctx = get_services()

    shortlist = ctx.planning.get_shortlist()
    if not shortlist.dish_uids:
        console.print("[yellow]Shortlist is empty[/yellow]")
        console.print("Use 'meal plan shortlist add <dish>' to add dishes")
        return

    # Resolve UIDs to dish names
    all_dishes = ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}

    table = Table(title=f"Shortlist ({len(shortlist)} dishes)")
    table.add_column("Name")
    table.add_column("Cuisine")
    table.add_column("Region")
    table.add_column("Categories")

    for uid in shortlist.dish_uids:
        dish = dish_map.get(uid)
        if dish:
            table.add_row(
                dish.name,
                dish.cuisine.value,
                dish.region.value,
                ", ".join(c.value for c in dish.categories),
            )
        else:
            table.add_row(f"[dim]{uid}[/dim]", "[red]Not found[/red]", "", "")

    console.print(table)


@shortlist_app.command("clear")
def shortlist_clear():
    """Clear all dishes from the shortlist."""
    ctx = get_services()

    ctx.planning.clear_shortlist()
    console.print("[green]Shortlist cleared[/green]")


# === Plan Commands ===


@app.command("create")
def create(
    name: str = typer.Argument(..., help="Plan name (e.g., 'January 2025')"),
    weeks: int = typer.Option(4, "--weeks", "-w", help="Number of weeks"),
    dishes_per_week: int = typer.Option(4, "--per-week", "-p", help="Dishes per week"),
):
    """Create a meal plan from the shortlist.

    Distributes dishes across weeks to maximize:
    - Food category diversity (greens, grains, fermented, etc.)
    - Cuisine novelty (Korean, Thai, Italian, etc.)
    - Regional balance (2 Eastern + 2 Western per week)
    """
    ctx = get_services()

    # Get shortlist
    shortlist = ctx.planning.get_shortlist()
    if not shortlist.dish_uids:
        console.print("[red]Shortlist is empty![/red]")
        console.print("Add dishes with: meal plan shortlist add <dish>")
        raise typer.Exit(1)

    # Resolve shortlist UIDs to dishes
    all_dishes = ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}
    dishes = [dish_map[uid] for uid in shortlist.dish_uids if uid in dish_map]

    if not dishes:
        console.print("[red]No valid dishes in shortlist[/red]")
        raise typer.Exit(1)

    # Create plan
    plan, result = ctx.planning.create_plan(
        name=name,
        dishes=dishes,
        weeks=weeks,
        dishes_per_week=dishes_per_week,
    )

    console.print(f"[bold green]Created plan: {plan.name}[/bold green]")
    console.print(f"  UID: {plan.uid}")
    console.print(f"  Weeks: {plan.num_weeks}")
    console.print(f"  Total dishes: {plan.total_dishes}")

    if result.discarded:
        console.print(f"\n[yellow]Discarded {len(result.discarded)} dishes (overflow)[/yellow]")
    if result.reused:
        console.print(f"[cyan]Reused {len(result.reused)} dishes (to fill weeks)[/cyan]")

    console.print()
    _show_plan_table(plan, dish_map)


@app.command("show")
def show(
    name: str = typer.Argument(..., help="Plan name or UID"),
):
    """Show a meal plan."""
    ctx = get_services()

    # Try by UID first, then by name
    result = ctx.planning.get_plan(name)
    if result.is_err():
        result = ctx.planning.get_plan_by_name(name)

    if result.is_err():
        console.print(f"[red]Plan not found: {name}[/red]")
        raise typer.Exit(1)

    plan = result.unwrap()

    # Get dish map for display
    all_dishes = ctx.catalogue.list_dishes()
    dish_map = {d.uid: d for d in all_dishes}

    console.print(f"[bold]{plan.name}[/bold]")
    console.print(f"  UID: {plan.uid}")
    console.print(f"  Weeks: {plan.num_weeks}")
    console.print()
    _show_plan_table(plan, dish_map)


@app.command("list")
def list_plans():
    """List all meal plans."""
    ctx = get_services()
    plans = ctx.planning.list_plans()

    if not plans:
        console.print("[yellow]No meal plans[/yellow]")
        console.print("Create one with: meal plan create <name>")
        return

    table = Table(title="Meal Plans")
    table.add_column("UID", style="dim")
    table.add_column("Name")
    table.add_column("Weeks")
    table.add_column("Total Dishes")

    for plan in plans:
        table.add_row(
            plan.uid,
            plan.name,
            str(plan.num_weeks),
            str(plan.total_dishes),
        )

    console.print(table)


@app.command("delete")
def delete(
    name: str = typer.Argument(..., help="Plan name or UID to delete"),
):
    """Delete a meal plan."""
    ctx = get_services()

    # Try by UID first, then by name
    result = ctx.planning.get_plan(name)
    if result.is_err():
        result = ctx.planning.get_plan_by_name(name)

    if result.is_err():
        console.print(f"[red]Plan not found: {name}[/red]")
        raise typer.Exit(1)

    plan = result.unwrap()
    ctx.planning.delete_plan(plan.uid)
    console.print(f"[green]Deleted plan: {plan.name}[/green]")


def _show_plan_table(plan, dish_map: dict):
    """Display a plan as a table."""
    table = Table(title=f"Meal Plan: {plan.name}")
    table.add_column("Week", style="bold")
    table.add_column("Dishes")

    for week_idx, week in enumerate(plan.weeks, 1):
        dish_names = []
        for uid in week.dishes:
            dish = dish_map.get(uid)
            if dish:
                dish_names.append(f"{dish.name} ({dish.cuisine.value})")
            else:
                dish_names.append(f"[dim]{uid}[/dim]")

        table.add_row(
            f"Week {week_idx}",
            "\n".join(dish_names) if dish_names else "[dim]Empty[/dim]",
        )

    console.print(table)
