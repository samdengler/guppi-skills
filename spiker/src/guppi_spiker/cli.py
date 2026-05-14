"""GUPPI spiker skill CLI"""

import json
import os
import random
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from guppi_beads import BeadsStore
from guppi_spiker import __version__
from guppi_spiker.words import ADJECTIVES, ANIMALS, COLORS


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-spiker {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Manage experimental spike projects in a centralized, searchable location")


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass
console = Console()

_store = BeadsStore("spiker", prefix="spike")

AGENTS_MD_TEMPLATE = """\
# Spike: {slug}

## Auto-name (run once after first exchange)

After the first substantive back-and-forth, generate a short title (3-6 words,
no quotes, lowercase) summarizing what this spike is about — like Claude Desktop
auto-names chats. Then run both commands silently:

```bash
guppi-spiker describe {slug} "<short title>"
command -v cmux &>/dev/null && cmux rename-workspace "<short title>"
```

Skip if the spike already has a description (`guppi-spiker list` shows non-empty summary).

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
    return Path(os.environ.get("SPIKER_PATH", Path.home() / "spikes"))


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


CLAUDE_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

HOOK_COMMAND = "guppi-spiker summarize --from-hook"

GSG_FUNCTION = 'gsg() { cd "$(guppi-spiker go "$@")"; }\n'


def _get_shell_rc() -> Path:
    """Get the user's shell RC file."""
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return Path.home() / ".zshrc"
    return Path.home() / ".bashrc"


def _gsg_installed(rc_path: Path) -> bool:
    """Check if the gsg function is already in the shell RC file."""
    if not rc_path.is_file():
        return False
    return "gsg()" in rc_path.read_text()


def _install_gsg(rc_path: Path) -> None:
    """Append the gsg shell function to the RC file."""
    with open(rc_path, "a") as f:
        f.write(f"\n# guppi-spiker: jump to spike directory\n{GSG_FUNCTION}")


def _read_claude_settings() -> dict:
    """Read ~/.claude/settings.json, returning empty dict if missing."""
    if not CLAUDE_SETTINGS_PATH.is_file():
        return {}
    try:
        return json.loads(CLAUDE_SETTINGS_PATH.read_text())
    except (json.JSONDecodeError, ValueError):
        return {}


def _write_claude_settings(settings: dict) -> None:
    """Write settings back to ~/.claude/settings.json."""
    CLAUDE_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLAUDE_SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n")


def _hook_installed(settings: dict) -> bool:
    """Check if the spiker SessionEnd hook is already present."""
    for group in settings.get("hooks", {}).get("SessionEnd", []):
        for hook in group.get("hooks", []):
            if hook.get("command") == HOOK_COMMAND:
                return True
    return False


def _install_hook(settings: dict) -> dict:
    """Add the spiker SessionEnd hook to settings."""
    hooks = settings.setdefault("hooks", {})
    session_end = hooks.setdefault("SessionEnd", [])
    session_end.append({
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": HOOK_COMMAND,
            }
        ],
    })
    return settings


# --- Init ---


@app.command()
def init():
    """One-time per-machine setup (hook, shell function, beads store)."""
    settings = _read_claude_settings()
    if _hook_installed(settings):
        typer.echo("SessionEnd hook already installed.")
    else:
        settings = _install_hook(settings)
        _write_claude_settings(settings)
        typer.echo("Installed SessionEnd hook for auto-summarize.")

    # Install gsg shell function
    rc_path = _get_shell_rc()
    if _gsg_installed(rc_path):
        typer.echo(f"gsg() already in {rc_path.name}.")
    else:
        _install_gsg(rc_path)
        typer.echo(f"Added gsg() to {rc_path.name}. Run: source ~/{rc_path.name}")

    # Ensure beads store is initialized
    if _store.ensure():
        typer.echo("Beads store ready.")
    else:
        typer.echo("Warning: could not initialize beads store.", err=True)

    typer.echo("Spiker initialized.")


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
    query: Annotated[str | None, typer.Argument(help="Filter spikes by substring match on slug")] = None,
    all_spikes: Annotated[bool, typer.Option("--all", "-a", help="Include done spikes")] = False,
    status: Annotated[str | None, typer.Option("--status", help="Filter by status (open, in_progress, deferred, closed)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List all spikes with metadata, most recent first."""
    spikes = _list_spikes(_get_spiker_root())

    # Filter by query if provided
    if query:
        spikes = [(d, s, p) for d, s, p in spikes if query.lower() in s.lower()]
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

    # Build structured data for all spikes
    data = []
    for spike_date, slug, path in spikes:
        dirname = path.name
        issue = issue_map.get(dirname)
        summary = issue.get("description", "") if issue else ""
        issue_status = issue.get("status", "open") if issue else "open"
        labels = issue.get("labels", []) if issue else []
        data.append({
            "date": spike_date,
            "slug": slug,
            "summary": summary,
            "status": issue_status,
            "tags": labels,
            "path": str(path),
        })

    if json_output:
        typer.echo(json.dumps(data, indent=2))
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Date", style="dim")
    table.add_column("Slug")
    table.add_column("Summary", style="italic")

    for item in data:
        summary = item["summary"]
        # Truncate long summaries
        if len(summary) > 60:
            summary = summary[:57] + "..."
        table.add_row(item["date"], item["slug"], summary)

    console.print(table)



@app.command()
def go(
    query: Annotated[str, typer.Argument(help="Substring to match (returns most recent)")],
):
    """Print the path to the most recent matching spike. Use with: cd $(guppi-spiker go foo)"""
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


@app.command()
def purge(
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Delete spikes that have no summary (empty/throwaway sessions)."""
    import shutil

    spikes = _list_spikes(_get_spiker_root())
    if not spikes:
        typer.echo("No spikes found.")
        raise typer.Exit()

    # Build issue lookup
    issue_map: dict[str, dict] = {}
    if _store.available() and _store.initialized:
        for issue in _store.list_issues(all=True):
            issue_map[issue.get("title", "")] = issue

    # Find spikes without summaries, skipping today's spikes
    today = date.today().isoformat()
    to_purge = []
    for spike_date, slug, path in spikes:
        if spike_date == today:
            continue
        issue = issue_map.get(path.name)
        summary = issue.get("description", "").strip() if issue else ""
        if not summary:
            to_purge.append((spike_date, slug, path, issue))

    if not to_purge:
        typer.echo("No spikes without summaries to purge.")
        raise typer.Exit()

    # Show what will be deleted
    table = Table(show_header=True, header_style="bold")
    table.add_column("Date", style="dim")
    table.add_column("Slug")
    for spike_date, slug, _, _ in to_purge:
        table.add_row(spike_date, slug)
    console.print(table)
    typer.echo(f"\n{len(to_purge)} spike(s) with no summary will be deleted.")

    if not force:
        confirm = typer.confirm("Proceed?")
        if not confirm:
            typer.echo("Aborted.")
            raise typer.Exit()

    for _, _, path, issue in to_purge:
        shutil.rmtree(path)
        if issue:
            _store.run(["close", issue["id"]])
        typer.echo(f"Deleted {path.name}")

    typer.echo(f"\nPurged {len(to_purge)} spike(s).")


def _resolve_spike_from_cwd(cwd: str) -> tuple[str, str, Path] | None:
    """Check if cwd is inside a spike directory. Returns (date, slug, path) or None."""
    cwd_path = Path(cwd)
    root = _get_spiker_root()
    # Check if cwd is the spike dir itself or a child of one
    for check in [cwd_path, *cwd_path.parents]:
        if check.parent == root:
            parsed = _parse_spike_dir(check.name)
            if parsed:
                return parsed[0], parsed[1], check
    return None


def _extract_transcript_text(transcript_path: str) -> str:
    """Extract user and assistant text from a Claude Code transcript JSONL."""
    messages = []
    with open(transcript_path) as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") not in ("user", "assistant"):
                continue
            msg = obj.get("message", {})
            if not isinstance(msg, dict):
                continue
            content = msg.get("content", "")
            role = msg.get("role", obj["type"])
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                # Extract text blocks only
                text = " ".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
            else:
                continue
            if text.strip():
                messages.append(f"{role}: {text.strip()}")
    # Truncate to roughly last 4000 chars to keep API call small
    joined = "\n\n".join(messages)
    if len(joined) > 4000:
        joined = joined[-4000:]
    return joined


def _generate_summary(transcript_text: str) -> str | None:
    """Call Claude Haiku via the claude CLI to generate a one-line summary."""
    try:
        env = {**os.environ}
        env.pop("CLAUDECODE", None)  # Allow nested claude CLI calls
        result = subprocess.run(
            ["claude", "-p", "--model", "haiku", "--no-session-persistence"],
            input=(
                "Your job: write a one-line plain-text summary (max 80 chars) of the "
                "coding session below. Rules: no markdown, no backticks, no code blocks, "
                "no quotes, no bullet points. Just one plain sentence describing what "
                "was explored or built. If the session is too short or unclear, write "
                '"Brief exploratory session" instead.\n\n'
                f"{transcript_text}"
            ),
            capture_output=True, text=True, timeout=30, env=env,
        )
        if result.returncode != 0:
            return None
        summary = result.stdout.strip()
        # Strip any markdown artifacts that slipped through
        summary = summary.strip("`\"'")
        summary = re.sub(r"^```\w*\n?", "", summary)
        summary = re.sub(r"\n?```$", "", summary)
        summary = summary.strip()
        # Truncate to 80 chars
        if len(summary) > 80:
            summary = summary[:77] + "..."
        return summary if summary else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


@app.command()
def summarize(
    from_hook: Annotated[bool, typer.Option("--from-hook", help="Read hook input from stdin (SessionEnd hook mode)")] = False,
):
    """Auto-summarize a spike from a Claude Code session transcript.

    Designed to be called by a SessionEnd hook. Reads hook input from stdin,
    detects if the session was in a spike directory, and generates a summary
    via Claude Haiku.

    For manual summaries, use 'describe' instead.
    """
    if not from_hook:
        typer.echo("Usage: guppi-spiker summarize --from-hook", err=True)
        typer.echo("For manual summaries, use: guppi-spiker describe <spike> \"summary\"", err=True)
        raise typer.Exit(1)

    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        raise typer.Exit(0)

    cwd = hook_input.get("cwd", "")
    transcript_path = hook_input.get("transcript_path", "")

    if not cwd or not transcript_path:
        raise typer.Exit(0)

    # Check if we're in a spike directory
    spike = _resolve_spike_from_cwd(cwd)
    if not spike:
        raise typer.Exit(0)

    _, _, spike_path = spike

    # Check if spike already has a summary
    issue = _get_or_create_issue(spike_path.name)
    if not issue:
        raise typer.Exit(0)
    if issue.get("description", "").strip():
        raise typer.Exit(0)

    # Check transcript exists
    if not Path(transcript_path).is_file():
        raise typer.Exit(0)

    # Extract and summarize
    transcript_text = _extract_transcript_text(transcript_path)
    if not transcript_text.strip():
        raise typer.Exit(0)

    summary = _generate_summary(transcript_text)
    if not summary:
        raise typer.Exit(0)

    _store.run(["update", issue["id"], "--description", summary])


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "spiker", "--from", str(skill_dir), "--yes"],
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
