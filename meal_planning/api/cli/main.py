"""Meal Planning CLI.

Command-line interface for meal planning operations.
Uses nested subcommands organized by domain.
"""

from __future__ import annotations

import typer
from rich.console import Console

from meal_planning.api.cli.commands import catalogue, planning, analysis, context
from meal_planning.core.context.models import UserContext

app = typer.Typer(
    name="meal",
    help="AI-powered meal planning CLI",
    no_args_is_help=True,
)
console = Console()

# Register subcommand groups
app.add_typer(catalogue.app, name="catalogue")
app.add_typer(planning.app, name="plan")
app.add_typer(analysis.app, name="analysis")
app.add_typer(context.app, name="context")


@app.command()
def seed():
    """Seed sample user contexts (dishes are auto-loaded as defaults)."""
    from meal_planning.app import get_app_context

    ctx = get_app_context()

    # Add sample user contexts
    vegetarian = UserContext(
        category="dietary",
        context="We are vegetarian. We do not eat any meat, but do eat dairy and eggs.",
    )
    location = UserContext(
        category="location",
        context="We live in Johor Bahru, Malaysia. We prefer local ingredients.",
    )

    for user_context in [vegetarian, location]:
        ctx.context.add_context(user_context)
    ctx.context.save()
    console.print("[green]Added 2 sample contexts[/green]")

    # Show dish count (defaults are auto-loaded)
    dish_count = len(ctx.catalogue.list_dishes())
    console.print(f"[dim]Catalogue has {dish_count} dishes (defaults auto-loaded)[/dim]")

    console.print("\n[bold green]Seed complete![/bold green]")


@app.command()
def reset(
    full: bool = typer.Option(
        False, "--full", help="Also remove user-created dishes"
    ),
):
    """Reset catalogue to default dishes."""
    from meal_planning.app import get_app_context

    ctx = get_app_context()

    before = len(ctx.catalogue.list_dishes())
    count = ctx.catalogue.reset_to_defaults(keep_user_additions=not full)

    if full:
        console.print(f"[green]Full reset: {before} -> {count} dishes[/green]")
    else:
        console.print(f"[green]Reset: {before} -> {count} dishes (kept user additions)[/green]")


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


@app.command()
def dash(
    port: int = typer.Option(8050, "--port", "-p", help="Port to run on"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """Launch the Dash web interface (Mantine UI)."""
    from meal_planning.api.dash.app import app as dash_app

    console.print(f"[green]Starting Dash app at http://localhost:{port}[/green]")
    dash_app.run(debug=debug, port=port)


def main():
    """Entry point for the CLI."""
    # Initialize app context before running commands
    from meal_planning.app import initialize_app

    initialize_app()
    app()


if __name__ == "__main__":
    main()
