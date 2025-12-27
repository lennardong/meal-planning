"""Context CLI commands.

Commands for managing user contexts (preferences).
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from meal_planning.core.context.models import VOUserContext

app = typer.Typer(
    name="context",
    help="Manage user preferences and constraints",
    no_args_is_help=True,
)
console = Console()


def get_services():
    """Get services from app context."""
    from meal_planning.app import get_app_context

    return get_app_context()


@app.command("add")
def add_context(
    text: str = typer.Argument(..., help="Context description"),
    category: Optional[str] = typer.Option(
        None, "--category", "-c", help="Category (dietary, location, etc.)"
    ),
):
    """Add a user context (preference/constraint)."""
    ctx = get_services()

    context = VOUserContext(
        context=text,
        category=category,
    )

    result = ctx.context.add_context(context)
    if result.is_ok():
        ctx.context.save()
        console.print(f"[green]Added context: {context.uid}[/green]")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_contexts():
    """List all user contexts (preferences)."""
    ctx = get_services()

    contexts = ctx.context.list_contexts()

    if not contexts:
        console.print("[yellow]No contexts configured[/yellow]")
        return

    table = Table(title="User Contexts")
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


@app.command("delete")
def delete_context(
    uid: str = typer.Argument(..., help="Context UID to delete"),
):
    """Delete a user context."""
    ctx = get_services()

    result = ctx.context.delete_context(uid)
    if result.is_ok():
        ctx.context.save()
        console.print(f"[green]Deleted context: {uid}[/green]")
    else:
        console.print(f"[red]Error: {result.error}[/red]")
        raise typer.Exit(1)
