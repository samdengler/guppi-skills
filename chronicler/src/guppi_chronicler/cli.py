"""GUPPI chronicler skill CLI"""

import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from . import __version__, config
from .dates import parse_date
from .sources import ADAPTER_TYPES, HistoryEntry, get_adapter


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-chronicler {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Research historical events from local history sources")


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass
console = Console()

# --- Source management subcommand group ---

source_app = typer.Typer(help="Manage history sources")
app.add_typer(source_app, name="source")


@source_app.command("list")
def source_list():
    """List registered sources and their status."""
    sources = config.get_sources()
    if not sources:
        console.print("No sources registered. Run 'guppi-chronicler source detect' to get started.")
        return

    table = Table()
    table.add_column("Name")
    table.add_column("Type")
    table.add_column("Enabled")
    table.add_column("Available")
    table.add_column("Path")

    for name, src in sources.items():
        adapter = get_adapter(name, src["type"], src.get("path"))
        avail = adapter.available()
        table.add_row(
            name,
            src["type"],
            "yes" if src.get("enabled", True) else "no",
            "yes" if avail else "[red]no[/red]",
            src.get("path") or "(default)",
        )

    console.print(table)


@source_app.command()
def add(
    name: Annotated[str, typer.Argument(help="Name for this source")],
    type: Annotated[str, typer.Option("--type", "-t", help="Source type (chrome, terminal)")],
    path: Annotated[str | None, typer.Option("--path", "-p", help="Override default data path")] = None,
):
    """Register a new history source."""
    if type not in ADAPTER_TYPES:
        console.print(f"[red]Unknown source type: '{type}'[/red]")
        console.print(f"Available types: {', '.join(ADAPTER_TYPES)}")
        raise typer.Exit(1)

    try:
        config.add_source(name, type, path)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    console.print(f"Source '{name}' registered (type={type})")

    # Auto-run init check
    adapter = get_adapter(name, type, path)
    issues = adapter.check_prereqs()
    if issues:
        console.print()
        console.print("[yellow]Prerequisites:[/yellow]")
        for issue in issues:
            console.print(f"  {issue}")
        console.print()
        console.print(f"Run 'guppi-chronicler source init {name} --apply' to fix automatically.")
    elif adapter.available():
        console.print("[green]Source is ready.[/green]")


@source_app.command()
def remove(
    name: Annotated[str, typer.Argument(help="Source name to remove")],
):
    """Unregister a history source."""
    try:
        config.remove_source(name)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    console.print(f"Source '{name}' removed")


@source_app.command()
def enable(
    name: Annotated[str, typer.Argument(help="Source name to enable")],
):
    """Enable a registered source."""
    try:
        config.set_source_enabled(name, True)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    console.print(f"Source '{name}' enabled")


@source_app.command()
def disable(
    name: Annotated[str, typer.Argument(help="Source name to disable")],
):
    """Disable a registered source."""
    try:
        config.set_source_enabled(name, False)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)
    console.print(f"Source '{name}' disabled")


@source_app.command()
def detect(
    apply: Annotated[bool, typer.Option("--apply", help="Auto-register detected sources")] = False,
):
    """Scan for available history sources on this machine."""
    existing = config.get_sources()
    found: list[tuple[str, str, str]] = []  # (name, type, path)

    for type_name, adapter_cls in ADAPTER_TYPES.items():
        path = adapter_cls.detect()
        if path:
            found.append((type_name, type_name, path))

    if not found:
        console.print("No history sources detected on this machine.")
        return

    for name, type_name, path in found:
        if name in existing:
            console.print(f"  {name}: already registered")
        elif apply:
            config.add_source(name, type_name)
            console.print(f"  {name}: [green]registered[/green] ({path})")
        else:
            console.print(f"  {name}: found ({path})")

    if not apply and any(name not in existing for name, _, _ in found):
        console.print()
        console.print("Run with --apply to register detected sources.")


@source_app.command()
def init(
    name: Annotated[str, typer.Argument(help="Source name to initialize")],
    apply: Annotated[bool, typer.Option("--apply", help="Apply changes automatically")] = False,
):
    """Check and fix prerequisites for a source."""
    src = config.get_source(name)
    if src is None:
        console.print(f"[red]Source '{name}' not found[/red]")
        raise typer.Exit(1)

    adapter = get_adapter(name, src["type"], src.get("path"))
    console.print(f"Checking prerequisites for '{name}'...")
    console.print()

    issues = adapter.check_prereqs()
    if not issues:
        console.print("[green]All prerequisites met. Source is ready.[/green]")
        return

    for issue in issues:
        console.print(f"  {issue}")

    if apply:
        console.print()
        actions = adapter.apply_prereqs()
        if actions:
            for action in actions:
                console.print(f"  [green]{action}[/green]")
        else:
            console.print("  [yellow]No automatic fixes available. Follow the instructions above.[/yellow]")
    else:
        console.print()
        console.print(f"Run 'guppi-chronicler source init {name} --apply' to fix automatically.")


# --- Search command ---


@app.command()
def search(
    query: Annotated[str | None, typer.Argument(help="Text to search for")] = None,
    source: Annotated[str | None, typer.Option("--source", "-s", help="Search a specific source")] = None,
    since: Annotated[str | None, typer.Option("--since", help="Results after this date/time")] = None,
    until: Annotated[str | None, typer.Option("--until", help="Results before this date/time")] = None,
    limit: Annotated[int, typer.Option("--limit", "-n", help="Max results")] = 50,
    timeout: Annotated[float, typer.Option("--timeout", "-t", help="Max seconds to wait")] = 10.0,
):
    """Search history across all enabled sources."""
    # Parse dates
    since_dt: datetime | None = None
    until_dt: datetime | None = None
    try:
        if since:
            since_dt = parse_date(since)
        if until:
            until_dt = parse_date(until)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1)

    # Determine which sources to search
    if source:
        src = config.get_source(source)
        if src is None:
            console.print(f"[red]Source '{source}' not found[/red]")
            raise typer.Exit(1)
        if not src.get("enabled", True):
            console.print(f"[yellow]Source '{source}' is disabled[/yellow]")
            raise typer.Exit(1)
        sources_to_search = {source: src}
    else:
        sources_to_search = config.get_enabled_sources()

    if not sources_to_search:
        console.print("No sources configured. Run 'guppi-chronicler source detect --apply' to get started.")
        return

    # Search concurrently with timeout
    all_entries: list[HistoryEntry] = []
    source_status: dict[str, str] = {}
    deadline = time.monotonic() + timeout

    def _search_source(name: str, src: dict) -> tuple[str, list[HistoryEntry]]:
        adapter = get_adapter(name, src["type"], src.get("path"))
        if not adapter.available():
            return name, []
        return name, adapter.search(query, since_dt, until_dt, limit)

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_search_source, name, src): name
            for name, src in sources_to_search.items()
        }

        for future in as_completed(futures, timeout=max(0, deadline - time.monotonic())):
            name = futures[future]
            try:
                _, entries = future.result()
                all_entries.extend(entries)
                source_status[name] = "ok"
            except Exception as e:
                source_status[name] = f"error: {e}"

    # Mark timed-out sources
    for name in sources_to_search:
        if name not in source_status:
            source_status[name] = "timed out"

    if not all_entries:
        console.print("No results found.")
        _print_source_status(source_status)
        return

    # Sort: dated entries by timestamp (newest first), undated at the end
    dated = [e for e in all_entries if e.timestamp is not None]
    undated = [e for e in all_entries if e.timestamp is None]
    dated.sort(key=lambda e: e.timestamp, reverse=True)  # type: ignore[arg-type]

    # Apply global limit
    combined = (dated + undated)[:limit]

    # Render table
    table = Table()
    table.add_column("Time")
    table.add_column("Source")
    table.add_column("Kind")
    table.add_column("Summary", max_width=80)

    in_undated = False
    for entry in combined:
        if entry.timestamp is None and not in_undated:
            in_undated = True
            table.add_section()

        time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if entry.timestamp else "—"
        table.add_row(time_str, entry.source, entry.kind, entry.summary)

    console.print(table)
    _print_source_status(source_status)


def _print_source_status(status: dict[str, str]) -> None:
    """Print the source status footer."""
    parts = []
    for name, s in status.items():
        if s == "ok":
            parts.append(f"{name} (ok)")
        elif s == "timed out":
            parts.append(f"[yellow]{name} (timed out)[/yellow]")
        else:
            parts.append(f"[red]{name} ({s})[/red]")
    console.print()
    console.print(f"Sources: {', '.join(parts)}")


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli"""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "chronicler", "--from", str(skill_dir), "--yes"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        typer.echo(result.stdout.strip())
    else:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)


@skill_app.command()
def show():
    """Display SKILL.md contents"""
    skill_md = _get_skill_md_path()
    typer.echo(skill_md.read_text())


def _get_skill_md_path() -> Path:
    """Locate SKILL.md bundled in the package"""
    package_dir = Path(__file__).parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        # Fallback: look in the skill root (development mode)
        skill_md = package_dir.parent.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
