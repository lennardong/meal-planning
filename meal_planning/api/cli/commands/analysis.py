"""Analysis CLI commands.

Commands for analyzing meal plans.
"""

from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="analysis",
    help="Analyze meal plans",
    no_args_is_help=True,
)
console = Console()


def get_services():
    """Get services from app context."""
    from meal_planning.app import get_app_context

    return get_app_context()


@app.command("variety")
def variety(
    month: str = typer.Argument(..., help="Month in format YYYY-MM"),
):
    """Analyze variety in a month's meal plan."""
    ctx = get_services()

    report = ctx.analysis.get_variety_report(month)

    if report is None:
        console.print(f"[yellow]No plan found for {month}[/yellow]")
        return

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
            result = ctx.catalogue.get_dish(uid)
            name = result.unwrap().name if result.is_ok() else uid
            console.print(f"  {name}: {count} times")


@app.command("suggest")
def suggest(
    month: str = typer.Argument(..., help="Month in format YYYY-MM"),
):
    """Get improvement suggestions for a meal plan."""
    ctx = get_services()

    suggestions = ctx.analysis.get_suggestions(month)

    if suggestions is None:
        console.print(f"[yellow]No plan found for {month}[/yellow]")
        return

    console.print(f"\n[bold]Suggestions for {month}[/bold]\n")

    if not suggestions:
        console.print("[green]No issues found. Great variety![/green]")
    else:
        for suggestion in suggestions:
            console.print(f"  - {suggestion}")
