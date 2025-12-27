"""Shopping CLI commands.

Commands for generating shopping lists.
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(
    name="shop",
    help="Generate shopping lists",
    no_args_is_help=True,
)
console = Console()


def get_services():
    """Get services from app context."""
    from meal_planning.app import get_app_context

    return get_app_context()


@app.command("list")
def shopping_list(
    month: str = typer.Argument(..., help="Month in format YYYY-MM"),
    week: Optional[int] = typer.Option(
        None, "--week", "-w", help="Week number (1-4). Omit for monthly list."
    ),
):
    """Generate shopping list for a week or month."""
    ctx = get_services()

    if week is not None:
        if not 1 <= week <= 4:
            console.print("[red]Week must be 1-4[/red]")
            raise typer.Exit(1)

        shopping = ctx.shopping.get_weekly_list(month, week)
        title = f"Shopping List for {month} Week {week}"
    else:
        shopping = ctx.shopping.get_monthly_list(month)
        title = f"Monthly Shopping List for {month}"

    if shopping is None:
        console.print(f"[yellow]No plan found for {month}[/yellow]")
        return

    console.print(f"\n[bold]{title}[/bold]\n")

    if shopping.bulk:
        console.print("[bold cyan]Bulk Items (Monthly Purchase):[/bold cyan]")
        for ing in shopping.bulk:
            console.print(f"  - {ing.name}")

    if shopping.weekly:
        console.print("\n[bold green]Weekly Items (Fresh Purchase):[/bold green]")
        for ing in shopping.weekly:
            console.print(f"  - {ing.name}")

    if not shopping.bulk and not shopping.weekly:
        console.print("[yellow]No items scheduled[/yellow]")
