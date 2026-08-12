"""GUPPI committer skill CLI"""

import subprocess
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from guppi_committer import __version__, vale
from guppi_committer.checks import check_message

HOOK_MARKER = "# guppi-committer hook"
HOOK_SCRIPT = f"""\
#!/bin/sh
{HOOK_MARKER}
exec guppi-committer check "$1"
"""


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-committer {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Standardize git commit messages with format and prose checks")
console = Console()


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass


# --- Domain commands ---


@app.command()
def check(
    file: Annotated[Optional[Path], typer.Argument(help="Commit message file (reads stdin if omitted)")] = None,
    strict: Annotated[bool, typer.Option("--strict", help="Fail on warnings as well as errors")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    use_vale: Annotated[Optional[bool], typer.Option("--vale/--no-vale", help="Also run Vale (default: auto, when installed and configured)")] = None,
    vale_config: Annotated[Optional[Path], typer.Option("--vale-config", help="Vale config file (default: the vale-setup config)")] = None,
):
    """Check a commit message against format and prose rules."""
    if file is not None:
        if not file.exists():
            typer.echo(f"Error: file not found: {file}", err=True)
            raise typer.Exit(2)
        text = file.read_text()
    else:
        text = sys.stdin.read()

    result = check_message(text)
    result.violations.extend(_vale_violations(text, use_vale, vale_config))
    result.violations.sort(key=lambda v: (v.line, v.rule))

    if json_output:
        import json

        typer.echo(json.dumps([v.as_dict() for v in result.violations], indent=2))
        raise typer.Exit(0 if result.ok(strict) else 1)

    for v in result.violations:
        color = "red" if v.severity == "error" else "yellow"
        console.print(f"line {v.line}: [{color}]{v.severity}[/{color}] {v.message} ({v.rule})")

    if result.ok(strict):
        summary = "Commit message OK"
        if result.warnings:
            summary += f" ({len(result.warnings)} warning{'s' if len(result.warnings) != 1 else ''})"
        console.print(f"[green]{summary}[/green]")
        raise typer.Exit(0)

    console.print(
        f"[red]Commit message rejected: {len(result.errors)} error{'s' if len(result.errors) != 1 else ''}, "
        f"{len(result.warnings)} warning{'s' if len(result.warnings) != 1 else ''}[/red]"
    )
    raise typer.Exit(1)


def _vale_violations(text: str, use_vale: Optional[bool], vale_config: Optional[Path]):
    """Run Vale when forced (--vale) or in auto mode when set up."""
    if use_vale is False:
        return []
    config = vale_config or vale.default_config()
    binary = vale.find_vale()
    if use_vale is None and (binary is None or config is None):
        return []
    if binary is None:
        typer.echo("Error: --vale given but vale is not installed (brew install vale)", err=True)
        raise typer.Exit(2)
    try:
        return vale.run(text, config)
    except RuntimeError as exc:
        typer.echo(f"Error: vale failed: {exc}", err=True)
        raise typer.Exit(2)


@app.command()
def vale_setup(
    sync: Annotated[bool, typer.Option("--sync/--no-sync", help="Run vale sync to download the Google package")] = True,
):
    """Write the starter Vale config (Google + STE styles). Idempotent."""
    ini = vale.write_config()
    typer.echo(f"Wrote Vale config: {ini}")

    if vale.find_vale() is None:
        typer.echo(
            "vale is not installed. Install it (brew install vale), then run: "
            f"vale sync --config {ini}"
        )
        return
    if sync:
        proc = subprocess.run(
            ["vale", "sync", f"--config={ini}"], capture_output=True, text=True
        )
        if proc.returncode != 0:
            typer.echo(f"Error: vale sync failed: {proc.stderr.strip()}", err=True)
            raise typer.Exit(1)
        typer.echo("Synced Vale packages (Google)")


@app.command()
def init(
    force: Annotated[bool, typer.Option("--force", "-f", help="Overwrite an existing commit-msg hook")] = False,
):
    """Install the commit-msg hook in the current git repository. Idempotent."""
    proc = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        typer.echo("Error: not inside a git repository", err=True)
        raise typer.Exit(1)

    hooks_dir = Path(proc.stdout.strip())
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "commit-msg"

    if hook_path.exists() and HOOK_MARKER not in hook_path.read_text() and not force:
        typer.echo(
            f"Error: {hook_path} exists and was not installed by guppi-committer. "
            "Use --force to overwrite.",
            err=True,
        )
        raise typer.Exit(1)

    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(0o755)
    typer.echo(f"Installed commit-msg hook: {hook_path}")


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli"""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "committer", "--from", str(skill_dir), "--yes"],
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
    skill_md = _get_skill_md_path()
    typer.echo(skill_md.read_text())


def _get_skill_md_path():
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
