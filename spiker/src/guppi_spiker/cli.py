"""GUPPI spiker skill CLI"""

import os
import random
import subprocess
from datetime import date
from pathlib import Path

from typing import Annotated

import typer

from guppi_spiker.words import ADJECTIVES, ANIMALS, COLORS

app = typer.Typer(help="Manage experimental spike projects in a centralized, searchable location")


def _get_spiker_root() -> Path:
    """Get the spike root directory from SPIKER_PATH env var or default."""
    return Path(os.environ.get("SPIKER_PATH", Path.home() / "src" / "spikes"))


def _generate_name() -> str:
    """Generate a random adjective-color-animal slug."""
    return f"{random.choice(ADJECTIVES)}-{random.choice(COLORS)}-{random.choice(ANIMALS)}"


def _parse_spike_dir(dirname: str) -> tuple[str, str] | None:
    """Parse a YYYY-MM-DD-slug directory name into (date, slug). Returns None if invalid."""
    parts = dirname.split("-", 3)
    if len(parts) < 4:
        return None
    date_part = f"{parts[0]}-{parts[1]}-{parts[2]}"
    slug = parts[3]
    return date_part, slug


def _list_spikes(root: Path) -> list[tuple[str, str, Path]]:
    """List all spikes as (date, slug, path) tuples, most recent first."""
    if not root.exists():
        return []
    spikes = []
    for entry in sorted(root.iterdir(), reverse=True):
        if not entry.is_dir():
            continue
        parsed = _parse_spike_dir(entry.name)
        if parsed:
            spikes.append((parsed[0], parsed[1], entry))
    return spikes


# --- Domain commands ---


@app.command()
def new(
    name: Annotated[str | None, typer.Argument(help="Slug for the spike directory (random if omitted)")] = None,
    git: Annotated[bool, typer.Option(help="Initialize a git repo")] = True,
):
    """Create a new spike directory."""
    root = _get_spiker_root()
    root.mkdir(parents=True, exist_ok=True)

    slug = name if name else _generate_name()
    dirname = f"{date.today().isoformat()}-{slug}"
    spike_path = root / dirname
    spike_path.mkdir(parents=True, exist_ok=True)

    if git:
        subprocess.run(["git", "init"], cwd=spike_path, capture_output=True)

    typer.echo(str(spike_path))


@app.command("list")
def list_spikes():
    """List all spikes, most recent first."""
    spikes = _list_spikes(_get_spiker_root())
    if not spikes:
        typer.echo("No spikes found.")
        raise typer.Exit()

    for spike_date, slug, _ in spikes:
        typer.echo(f"{spike_date}  {slug}")


@app.command()
def find(
    query: Annotated[str, typer.Argument(help="Substring to search for in spike names")],
):
    """Search spikes by substring match."""
    spikes = _list_spikes(_get_spiker_root())
    matches = [(d, s, p) for d, s, p in spikes if query.lower() in s.lower()]

    if not matches:
        typer.echo(f"No spikes matching '{query}'.")
        raise typer.Exit(1)

    for _, _, path in matches:
        typer.echo(str(path))


@app.command()
def path(
    query: Annotated[str, typer.Argument(help="Substring to match (returns most recent)")],
):
    """Print the path to the most recent matching spike."""
    spikes = _list_spikes(_get_spiker_root())
    for _, slug, spike_path in spikes:
        if query.lower() in slug.lower():
            typer.echo(str(spike_path))
            raise typer.Exit()

    typer.echo(f"No spikes matching '{query}'.", err=True)
    raise typer.Exit(1)


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    result = subprocess.run(
        ["guppi", "skill", "install", str(skill_md)],
        capture_output=True, text=True,
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
        # Fallback: look in the skill root (development mode)
        # package_dir = spiker/src/guppi_spiker → .parent.parent = spiker/
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
