"""GUPPI usher skill CLI.

Rank movie showtimes by format and find the best contiguous seats by your saved
preferences. Booking is human-in-the-loop: usher prints ranked options and a
deep link; you log in and pay.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from guppi_usher import __version__, prefs as prefs_mod, ranking, regal

console = Console()


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-usher {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Rank showtimes by format and find the best contiguous seats.")


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show version and exit",
                     callback=_version_callback, is_eager=True),
    ] = False,
):
    pass


# --------------------------------------------------------------------------- #
# init
# --------------------------------------------------------------------------- #
@app.command()
def init():
    """Seed your preferences file (idempotent)."""
    path = prefs_mod.ensure_seeded()
    console.print(f"Preferences ready at [cyan]{path}[/cyan]")


# --------------------------------------------------------------------------- #
# seats — fetch + rank a seat map for a known showtime session
# --------------------------------------------------------------------------- #
@app.command()
def seats(
    theatre: Annotated[str, typer.Option("--theatre", "-t", help="theatreCode, e.g. 1346")],
    session: Annotated[str, typer.Option("--session", "-s", help="sessionId from the seat-page URL")],
    tickets: Annotated[int, typer.Option("--tickets", "-n", help="Number of (contiguous) seats")] = 2,
    screen: Annotated[Optional[str], typer.Option("--screen", help="Screen label to apply saved picks")] = None,
    theatre_slug: Annotated[Optional[str], typer.Option("--theatre-slug", help="Prefs key, e.g. regal-atlantic-station")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Rank the best contiguous seats for a showtime (active Chrome tab must be on regmovies.com)."""
    try:
        seat_list = regal.fetch_seat_plan(theatre, session)
    except Exception as exc:  # browser bridge / network
        console.print(f"[red]Could not read seat plan:[/red] {exc}")
        raise typer.Exit(1)

    row_priority = None
    pick_note = ""
    if screen and theatre_slug:
        picks = prefs_mod.picks_for_screen(prefs_mod.load(), theatre_slug, screen)
        if picks:
            row_priority = _rows_in_order(picks)
            # try the exact saved pick first (as a contiguous group of `tickets`)
            wanted = [(_split_seat(p)) for p in picks[:tickets]]
            res = ranking.match_saved_pick(seat_list, wanted)
            pick_note = ("saved pick available" if res.available
                         else f"saved pick {res.note}; showing nearest")

    groups = ranking.find_best_seats(seat_list, tickets, row_priority=row_priority)
    avail = sum(1 for s in seat_list if s.available)

    if json_output:
        typer.echo(json.dumps({
            "theatre": theatre, "session": session, "tickets": tickets,
            "available": avail, "total": len(seat_list), "note": pick_note,
            "options": [{"row": g.row, "seats": g.labels,
                         "center_distance": round(g.center_distance, 2)} for g in groups[:5]],
        }, indent=2))
        return

    if pick_note:
        console.print(f"[dim]{pick_note}[/dim]")
    console.print(f"{avail}/{len(seat_list)} seats available")
    table = Table(title=f"Best {tickets}-seat options")
    table.add_column("#", justify="right")
    table.add_column("Seats")
    table.add_column("Off-center", justify="right")
    for i, g in enumerate(groups[:5], 1):
        table.add_row(str(i), ", ".join(g.labels), f"{g.center_distance:.1f}")
    if not groups:
        console.print("[yellow]No contiguous block of that size is available.[/yellow]")
    else:
        console.print(table)


# --------------------------------------------------------------------------- #
# showtimes — list showtimes for a movie at a theatre (experimental: live DOM)
# --------------------------------------------------------------------------- #
@app.command()
def showtimes(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List showtimes on the movie/theatre page currently open in Chrome (experimental)."""
    try:
        raw = regal.fetch_showtimes_raw()
    except Exception as exc:
        console.print(f"[red]Could not read showtimes:[/red] {exc}")
        raise typer.Exit(1)

    if json_output:
        typer.echo(json.dumps(raw, indent=2))
        return
    table = Table(title="Showtimes (current page)")
    table.add_column("Button id")
    table.add_column("Time")
    for r in raw:
        table.add_row(r.get("btnId", ""), r.get("time", ""))
    console.print(table)
    console.print("[dim]Format-per-showtime association is still being hardened "
                  "(guppi-skills-tmy).[/dim]")


# --------------------------------------------------------------------------- #
# find — end-to-end (experimental until live showtime/format extraction lands)
# --------------------------------------------------------------------------- #
@app.command()
def find(
    movie: Annotated[str, typer.Argument(help="Movie slug, e.g. backrooms-ho00021220")],
    theatre: Annotated[str, typer.Option("--theatre", "-t", help="theatreCode, e.g. 1346")],
    tickets: Annotated[int, typer.Option("--tickets", "-n", help="Number of contiguous seats")] = 2,
    after: Annotated[Optional[str], typer.Option("--after", help="Earliest start, e.g. 18:00")] = None,
    action: Annotated[bool, typer.Option("--action", help="Treat as an action movie (enables 4DX)")] = False,
):
    """Rank showtimes by format and propose best seats. (Experimental — see notes.)"""
    console.print(
        "[yellow]find is experimental.[/yellow] Live showtime+format extraction "
        "(guppi-skills-tmy) is not complete. For now:\n"
        f"  1. Open [cyan]{regal.movie_showtimes_url(movie, theatre)}[/cyan] in Chrome\n"
        "  2. Run [cyan]guppi-usher showtimes[/cyan] to list times\n"
        "  3. Click the chosen showtime, then [cyan]guppi-usher seats -t "
        f"{theatre} -s <sessionId> -n {tickets}[/cyan]"
    )
    if after:
        console.print(f"[dim]time filter requested: after {after}[/dim]")
    if action:
        console.print("[dim]action movie: 4DX eligible[/dim]")


# --------------------------------------------------------------------------- #
# prefs
# --------------------------------------------------------------------------- #
prefs_app = typer.Typer(help="View your saved preferences")
app.add_typer(prefs_app, name="prefs")


@prefs_app.command("show")
def prefs_show(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Show saved format and seat preferences."""
    data = prefs_mod.load()
    if json_output:
        typer.echo(json.dumps(data, indent=2))
        return
    console.print_json(data=data)


@prefs_app.command("path")
def prefs_path():
    """Print the preferences file path."""
    typer.echo(str(prefs_mod.prefs_path()))


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _split_seat(label: str) -> tuple[str, str]:
    """'K15' -> ('K', '15')."""
    i = 0
    while i < len(label) and label[i].isalpha():
        i += 1
    return label[:i], label[i:]


def _rows_in_order(picks: list[str]) -> list[str]:
    seen: list[str] = []
    for p in picks:
        row, _ = _split_seat(p)
        if row and row not in seen:
            seen.append(row)
    return seen


# --------------------------------------------------------------------------- #
# skill management
# --------------------------------------------------------------------------- #
skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli"""
    import subprocess

    skill_md = _get_skill_md_path()
    result = subprocess.run(
        ["guppi", "skills", "install", "usher", "--from", str(skill_md.parent), "--yes"],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        typer.echo(result.stdout.strip())
    else:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)


@skill_app.command()
def show():
    """Display SKILL.md contents"""
    typer.echo(_get_skill_md_path().read_text())


def _get_skill_md_path() -> Path:
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
