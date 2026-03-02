"""GUPPI spiker skill CLI"""

import os
import random
import re
import subprocess
from datetime import date
from pathlib import Path

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from guppi_beads import BeadsStore
from guppi_spiker.words import ADJECTIVES, ANIMALS, COLORS

app = typer.Typer(help="Manage experimental spike projects in a centralized, searchable location")
console = Console()

_store = BeadsStore("spiker", prefix="spike")

AGENTS_MD_TEMPLATE = """\
# Spike: {slug}

## Session Protocol

Before ending a session, update this spike's metadata:

```bash
guppi-spiker describe {slug} "one-line summary of what you explored"
guppi-spiker tag {slug} topic1 topic2
guppi-spiker done {slug}  # if the spike is complete
```
"""


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


def _resolve_spike(query: str) -> tuple[str, str, Path] | None:
    """Find the most recent spike matching query. Returns (date, slug, path) or None."""
    spikes = _list_spikes(_get_spiker_root())
    for d, s, p in spikes:
        if query.lower() in s.lower():
            return d, s, p
    return None


def _get_or_create_issue(dirname: str) -> dict | None:
    """Find or auto-create a beads issue for a spike dirname. Returns issue dict or None."""
    if not _store.ensure():
        return None
    issue = _store.find_by_title(dirname)
    if not issue:
        result = _store.run(["create", dirname])
        if result.returncode != 0:
            return None
        issue = _store.find_by_title(dirname)
    return issue


# --- Domain commands ---


def _find_existing(slug: str, root: Path) -> Path | None:
    """Find an existing spike directory with the given slug, regardless of date prefix."""
    if not root.is_dir():
        return None
    pattern = re.compile(rf"^\d{{4}}-\d{{2}}-\d{{2}}-{re.escape(slug)}$")
    matches = sorted(
        (d for d in root.iterdir() if d.is_dir() and pattern.match(d.name)),
        key=lambda d: d.name,
    )
    return matches[-1] if matches else None


@app.command()
def new(
    name: Annotated[str | None, typer.Argument(help="Slug for the spike directory (random if omitted)")] = None,
    git: Annotated[bool, typer.Option(help="Initialize a git repo")] = True,
    summary: Annotated[str | None, typer.Option("--summary", "-s", help="One-line summary of the spike")] = None,
):
    """Create a new spike directory (idempotent when name is provided).

    If a spike with the given name already exists, prints its path without
    creating a new directory. Designed for use with:

        cd $(guppi-spiker new my-experiment)
    """
    root = _get_spiker_root()

    # When a name is given, check for existing spike first (idempotent)
    if name:
        existing = _find_existing(name, root)
        if existing:
            typer.echo(str(existing))
            return

    root.mkdir(parents=True, exist_ok=True)

    slug = name if name else _generate_name()
    dirname = f"{date.today().isoformat()}-{slug}"
    spike_path = root / dirname
    spike_path.mkdir(parents=True, exist_ok=True)

    if git:
        subprocess.run(["git", "init"], cwd=spike_path, capture_output=True)

    # Write AGENTS.md
    agents_md = spike_path / "AGENTS.md"
    if not agents_md.exists():
        agents_md.write_text(AGENTS_MD_TEMPLATE.format(slug=slug))

    # Create beads issue
    if _store.ensure():
        args = ["create", dirname]
        if summary:
            args.extend(["--description", summary])
        _store.run(args)

    typer.echo(str(spike_path))


@app.command("list")
def list_spikes(
    all_spikes: Annotated[bool, typer.Option("--all", "-a", help="Include done spikes")] = False,
    status: Annotated[str | None, typer.Option("--status", help="Filter by status (open, in_progress, deferred, closed)")] = None,
):
    """List all spikes with metadata, most recent first."""
    spikes = _list_spikes(_get_spiker_root())
    if not spikes:
        typer.echo("No spikes found.")
        raise typer.Exit()

    # Build a lookup of beads issues by title (dirname)
    issue_map: dict[str, dict] = {}
    if _store.available() and _store.initialized:
        for issue in _store.list_issues(all=True):
            issue_map[issue.get("title", "")] = issue

    # Filter by status if beads is available
    if status or (not all_spikes and issue_map):
        filtered = []
        for spike_date, slug, path in spikes:
            dirname = path.name
            issue = issue_map.get(dirname)
            issue_status = issue.get("status", "open") if issue else "open"
            if status:
                if issue_status == status:
                    filtered.append((spike_date, slug, path))
            else:
                # Default: show everything except closed
                if issue_status != "closed":
                    filtered.append((spike_date, slug, path))
        spikes = filtered

    if not spikes:
        typer.echo("No spikes found.")
        raise typer.Exit()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Date", style="dim")
    table.add_column("Slug")
    table.add_column("Summary", style="italic")

    for spike_date, slug, path in spikes:
        dirname = path.name
        issue = issue_map.get(dirname)
        summary = issue.get("description", "") if issue else ""
        # Truncate long summaries
        if len(summary) > 60:
            summary = summary[:57] + "..."
        table.add_row(spike_date, slug, summary)

    console.print(table)


@app.command()
def find(
    query: Annotated[str, typer.Argument(help="Substring to search for in spike names and metadata")],
):
    """Search spikes by slug, summary, and tags."""
    spikes = _list_spikes(_get_spiker_root())
    slug_matches = {p.name for _, _, p in spikes if query.lower() in _.lower()}
    # _ above is slug — let me be explicit
    slug_matches = set()
    for _, slug, path in spikes:
        if query.lower() in slug.lower():
            slug_matches.add(path.name)

    # Also search beads if available
    beads_matches: set[str] = set()
    if _store.available() and _store.initialized:
        result = _store.run(["search", query, "--json"])
        if result.returncode == 0:
            import json
            try:
                for issue in json.loads(result.stdout):
                    beads_matches.add(issue.get("title", ""))
            except (json.JSONDecodeError, ValueError):
                pass

    # Merge: find spikes whose dirname is in either set
    all_match_dirnames = slug_matches | beads_matches
    matches = [(d, s, p) for d, s, p in spikes if p.name in all_match_dirnames]

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


@app.command()
def describe(
    query: Annotated[str, typer.Argument(help="Spike to update (substring match)")],
    summary: Annotated[str, typer.Argument(help="One-line summary")],
):
    """Set or update a spike's summary."""
    match = _resolve_spike(query)
    if not match:
        typer.echo(f"No spikes matching '{query}'.", err=True)
        raise typer.Exit(1)

    _, _, path = match
    issue = _get_or_create_issue(path.name)
    if not issue:
        typer.echo("Beads not available — cannot set summary.", err=True)
        raise typer.Exit(1)

    _store.run(["update", issue["id"], "--description", summary])
    typer.echo(f"Updated summary for {path.name}")


@app.command()
def tag(
    query: Annotated[str, typer.Argument(help="Spike to tag (substring match)")],
    tags: Annotated[list[str], typer.Argument(help="Tags to add")],
):
    """Add tags to a spike."""
    match = _resolve_spike(query)
    if not match:
        typer.echo(f"No spikes matching '{query}'.", err=True)
        raise typer.Exit(1)

    _, _, path = match
    issue = _get_or_create_issue(path.name)
    if not issue:
        typer.echo("Beads not available — cannot add tags.", err=True)
        raise typer.Exit(1)

    for t in tags:
        _store.run(["update", issue["id"], "--add-label", t])
    typer.echo(f"Tagged {path.name}: {', '.join(tags)}")


@app.command()
def park(
    query: Annotated[str, typer.Argument(help="Spike to park (substring match)")],
):
    """Park a spike (mark as deferred)."""
    match = _resolve_spike(query)
    if not match:
        typer.echo(f"No spikes matching '{query}'.", err=True)
        raise typer.Exit(1)

    _, _, path = match
    issue = _get_or_create_issue(path.name)
    if not issue:
        typer.echo("Beads not available — cannot park spike.", err=True)
        raise typer.Exit(1)

    _store.run(["update", issue["id"], "--status", "deferred"])
    typer.echo(f"Parked {path.name}")


@app.command()
def done(
    query: Annotated[str, typer.Argument(help="Spike to close (substring match)")],
):
    """Mark a spike as done (close the beads issue)."""
    match = _resolve_spike(query)
    if not match:
        typer.echo(f"No spikes matching '{query}'.", err=True)
        raise typer.Exit(1)

    _, _, path = match
    issue = _get_or_create_issue(path.name)
    if not issue:
        typer.echo("Beads not available — cannot close spike.", err=True)
        raise typer.Exit(1)

    _store.run(["close", issue["id"]])
    typer.echo(f"Done: {path.name}")


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skill", "install", "spiker", "--from", str(skill_dir), "--yes"],
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
