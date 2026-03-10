"""GUPPI tracker skill CLI"""

import json
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from guppi_beads import BeadsStore
from guppi_tracker import __version__


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-tracker {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Cross-project task and idea tracker built on beads")
console = Console()

_store = BeadsStore("tracker", prefix="trk")


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass


def _require_beads():
    """Ensure beads is available and initialized, or exit with error."""
    if not _store.available():
        typer.echo("Error: bd CLI not found. Install beads first.", err=True)
        raise typer.Exit(1)
    if not _store.ensure():
        typer.echo("Error: Failed to initialize beads.", err=True)
        raise typer.Exit(1)


# --- Domain commands ---


@app.command()
def add(
    title: Annotated[str, typer.Argument(help="Title of the item to track")],
    tag: Annotated[list[str] | None, typer.Option("--tag", "-t", help="Tags (repeatable)")] = None,
    note: Annotated[str | None, typer.Option("--note", "-n", help="Description or note")] = None,
):
    """Add a new tracked item."""
    _require_beads()

    args = ["create", title]
    if note:
        args.extend(["--description", note])
    if tag:
        args.extend(["--labels", ",".join(tag)])

    result = _store.run(args)
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    typer.echo(result.stdout.strip())


@app.command("list")
def list_items(
    tag: Annotated[str | None, typer.Option("--tag", "-t", help="Filter by tag")] = None,
    all_items: Annotated[bool, typer.Option("--all", "-a", help="Include closed items")] = False,
):
    """List tracked items."""
    _require_beads()

    args = ["list", "--json"]
    if all_items:
        args.append("--all")
    if tag:
        args.extend(["--label", tag])

    result = _store.run(args)
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    try:
        issues = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        issues = []

    if not issues:
        typer.echo("No items found.")
        raise typer.Exit()

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Tags", style="italic")

    for issue in issues:
        issue_id = issue.get("id", "")
        title = issue.get("title", "")
        labels = issue.get("labels", [])
        tags_str = ", ".join(labels) if labels else ""
        table.add_row(issue_id, title, tags_str)

    console.print(table)


@app.command()
def done(
    issue_id: Annotated[str, typer.Argument(help="Beads issue ID (e.g., trk-a3f)")],
):
    """Mark an item as done."""
    _require_beads()

    result = _store.run(["close", issue_id])
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Done: {issue_id}")


@app.command()
def tag(
    issue_id: Annotated[str, typer.Argument(help="Beads issue ID (e.g., trk-a3f)")],
    tags: Annotated[list[str], typer.Argument(help="Tags to add")],
):
    """Add tags to an item."""
    _require_beads()

    for t in tags:
        result = _store.run(["update", issue_id, "--add-label", t])
        if result.returncode != 0:
            typer.echo(f"Error: {result.stderr.strip()}", err=True)
            raise typer.Exit(1)

    typer.echo(f"Tagged {issue_id}: {', '.join(tags)}")


@app.command()
def show(
    issue_id: Annotated[str, typer.Argument(help="Beads issue ID (e.g., trk-a3f)")],
):
    """Show full details of an item."""
    _require_beads()

    result = _store.run(["show", issue_id])
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    typer.echo(result.stdout.strip())


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search text")],
):
    """Search items by title and description."""
    _require_beads()

    result = _store.run(["search", query])
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    output = result.stdout.strip()
    if not output:
        typer.echo(f"No items matching '{query}'.")
        raise typer.Exit(1)

    typer.echo(output)


@app.command()
def review():
    """Process inbox — walk through untagged items and tag, done, or skip them."""
    _require_beads()

    args = ["list", "--json", "--no-labels"]
    result = _store.run(args)
    if result.returncode != 0:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)

    try:
        issues = json.loads(result.stdout)
    except (json.JSONDecodeError, ValueError):
        issues = []

    if not issues:
        console.print("[green]Inbox zero![/green] Nothing to review.")
        raise typer.Exit()

    console.print(f"\n[bold]{len(issues)} item(s) to review[/bold]\n")

    for i, issue in enumerate(issues, 1):
        issue_id = issue.get("id", "")
        title = issue.get("title", "")

        console.print(f"[bold][{i}/{len(issues)}][/bold] {title}")
        console.print(f"  [dim]{issue_id}[/dim]")

        action = typer.prompt(
            "  (t)ag, (d)one, (s)kip, (q)uit",
            default="s",
        )

        if action.lower().startswith("t"):
            tags_input = typer.prompt("  Tags (space-separated)")
            for t in tags_input.split():
                _store.run(["update", issue_id, "--add-label", t])
            console.print(f"  [green]Tagged: {tags_input}[/green]")
        elif action.lower().startswith("d"):
            _store.run(["close", issue_id])
            console.print(f"  [green]Done[/green]")
        elif action.lower().startswith("q"):
            console.print("\nStopped.")
            raise typer.Exit()
        else:
            console.print(f"  [dim]Skipped[/dim]")

        console.print()

    console.print("[green]Review complete![/green]")


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "tracker", "--from", str(skill_dir), "--yes"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        typer.echo(result.stdout.strip())
    else:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)


@skill_app.command("show")
def show_skill():
    """Display SKILL.md contents."""
    skill_md = _get_skill_md_path()
    typer.echo(skill_md.read_text())


def _get_skill_md_path() -> Path:
    """Locate SKILL.md bundled in the package."""
    package_dir = Path(__file__).parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
