"""Planning CLI commands.

Commands for managing meal plans.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

from meal_planning.core.planning.enums import Day

app = typer.Typer(
    name="plan",
    help="Manage meal plans",
    no_args_is_help=True,
)
console = Console()


def get_services():
    """Get services from app context."""
    from meal_planning.app import get_app_context

    return get_app_context()


@app.command("show")
def show(
    month: str = typer.Argument(..., help="Month in format YYYY-MM (e.g., 2025-01)"),
):
    """Show the meal plan for a month."""
    ctx = get_services()
    summary = ctx.ai_assistant.get_plan_summary(month)

    if summary:
        console.print(summary)
    else:
        console.print(f"[yellow]No plan found for {month}[/yellow]")


@app.command("create")
def create(
    month: str = typer.Argument(..., help="Month in format YYYY-MM (e.g., 2025-01)"),
):
    """Create a new meal plan for a month."""
    ctx = get_services()

    result = ctx.planning.create_plan(month)
    if result.is_ok():
        ctx.planning.save()
        plan = result.unwrap()
        console.print(f"[green]Created plan: {plan.uid}[/green]")
    else:
        console.print(f"[yellow]Plan already exists for {month}[/yellow]")


@app.command("schedule")
def schedule(
    month: str = typer.Argument(..., help="Month in format YYYY-MM"),
    week: int = typer.Option(..., "--week", "-w", help="Week number (1-4)"),
    day: str = typer.Option(..., "--day", "-d", help="Day (Mon, Tue, etc.)"),
    dish: Optional[str] = typer.Option(
        None, "--dish", help="Dish name (omit to clear)"
    ),
):
    """Schedule a dish for a specific day."""
    ctx = get_services()

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

    # Ensure plan exists
    plan_result = ctx.planning.get_plan_for_month(month)
    if plan_result.is_err():
        # Create plan if it doesn't exist
        ctx.planning.create_plan(month)

    # Find dish UID
    dish_uid = None
    if dish:
        found = None
        for d in ctx.catalogue.list_dishes():
            if d.name.lower() == dish.lower():
                found = d
                break
        if not found:
            console.print(f"[red]Dish not found: {dish}[/red]")
            raise typer.Exit(1)
        dish_uid = found.uid

    # Schedule
    plan_uid = f"PLAN-{month}"
    result = ctx.planning.schedule_dish(plan_uid, week, day_enum, dish_uid)

    if result.is_ok():
        ctx.planning.save()
        if dish_uid:
            console.print(f"[green]Scheduled '{dish}' for {day} Week {week}[/green]")
        else:
            console.print(f"[green]Cleared {day} Week {week}[/green]")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)
