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
    plan: str = typer.Argument(..., help="Plan name or UID"),
):
    """Analyze variety in a meal plan."""
    ctx = get_services()

    report = ctx.analysis.get_variety_report(plan)

    if report is None:
        console.print(f"[yellow]No plan found: {plan}[/yellow]")
        return

    console.print(f"\n[bold]Variety Report for {plan}[/bold]\n")
    console.print(f"Variety Score: [bold]{report.variety_score}/100[/bold]")
    console.print(f"Unique Dishes: {report.unique_dish_count}")
    console.print(f"Total Dishes: {report.total_dish_count}")

    if report.cuisine_distribution:
        console.print("\n[bold]Cuisine Distribution:[/bold]")
        for cuisine, count in report.cuisine_distribution.items():
            console.print(f"  {cuisine}: {count}")

    if report.region_distribution:
        console.print("\n[bold]Region Distribution:[/bold]")
        for region, count in report.region_distribution.items():
            console.print(f"  {region}: {count}")

    if report.category_distribution:
        console.print("\n[bold]Category Distribution:[/bold]")
        for category, count in sorted(report.category_distribution.items(), key=lambda x: -x[1]):
            console.print(f"  {category}: {count}")

    if report.repeated_dishes:
        console.print("\n[bold yellow]Repeated Dishes (>2 times):[/bold yellow]")
        for uid, count in report.repeated_dishes.items():
            result = ctx.catalogue.get_dish(uid)
            name = result.unwrap().name if result.is_ok() else uid
            console.print(f"  {name}: {count} times")


@app.command("suggest")
def suggest(
    plan: str = typer.Argument(..., help="Plan name or UID"),
):
    """Get improvement suggestions for a meal plan."""
    ctx = get_services()

    suggestions = ctx.analysis.get_suggestions(plan)

    if suggestions is None:
        console.print(f"[yellow]No plan found: {plan}[/yellow]")
        return

    console.print(f"\n[bold]Suggestions for {plan}[/bold]\n")

    if not suggestions:
        console.print("[green]No issues found. Great variety![/green]")
    else:
        for suggestion in suggestions:
            console.print(f"  - {suggestion}")
