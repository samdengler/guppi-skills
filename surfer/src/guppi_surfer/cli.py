"""GUPPI surfer skill CLI"""

import subprocess
from pathlib import Path
from typing import Annotated

import typer

from guppi_surfer import __version__


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-surfer {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Chrome browser automation via AppleScript JavaScript execution")


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass

# --- Domain commands ---


@app.command()
def run(
    js: str = typer.Argument(help="JavaScript to execute in the active Chrome tab"),
):
    """Execute JavaScript in the active Chrome tab via AppleScript."""
    typer.echo("Not yet implemented.")
    raise typer.Exit(1)


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skill", "install", "surfer", "--from", str(skill_dir), "--yes"],
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
