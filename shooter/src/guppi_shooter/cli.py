"""GUPPI shooter skill CLI"""

import subprocess
from pathlib import Path
from typing import Annotated

import typer

from guppi_shooter import __version__


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-shooter {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Screenshot manager — set preferences and manage screen captures")


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass

# --- Domain commands ---


@app.command()
def prefs(
    location: Annotated[
        str | None, typer.Option("--location", "-l", help="Set screenshot save location")
    ] = None,
    format: Annotated[
        str | None,
        typer.Option("--format", "-f", help="Set screenshot format (png, jpg, tiff, etc.)"),
    ] = None,
    show: Annotated[
        bool, typer.Option("--show", "-s", help="Show current screenshot preferences")
    ] = False,
):
    """View or set macOS screenshot preferences."""
    if show or (location is None and format is None):
        _show_prefs()
        return

    if location is not None:
        _set_pref("location", location)

    if format is not None:
        _set_pref("type", format)


def _show_prefs():
    """Display current screenshot preferences."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Screenshot Preferences")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    prefs = {
        "location": _read_pref("location", "~/Desktop"),
        "type": _read_pref("type", "png"),
        "name": _read_pref("name", "Screenshot"),
        "disable-shadow": _read_pref("disable-shadow", "false"),
        "include-date": _read_pref("include-date", "true"),
        "show-thumbnail": _read_pref("show-thumbnail", "true"),
    }

    for key, value in prefs.items():
        table.add_row(key, str(value))

    console.print(table)


def _read_pref(key: str, default: str) -> str:
    """Read a screenshot preference from macOS defaults."""
    result = subprocess.run(
        ["defaults", "read", "com.apple.screencapture", key],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return default


def _set_pref(key: str, value: str):
    """Set a screenshot preference via macOS defaults."""
    subprocess.run(
        ["defaults", "write", "com.apple.screencapture", key, value],
        check=True,
    )
    typer.echo(f"Set {key} = {value}")


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "shooter", "--from", str(skill_dir), "--yes"],
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
    """Display SKILL.md contents."""
    skill_md = _get_skill_md_path()
    typer.echo(skill_md.read_text())


def _get_skill_md_path() -> Path:
    """Locate SKILL.md bundled in the package."""
    package_dir = Path(__file__).parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md = package_dir.parent.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
