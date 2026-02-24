"""GUPPI clipper skill CLI"""

import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

app = typer.Typer(help="Copy content to the system clipboard without whitespace noise")
console = Console(stderr=True)


def _get_clipboard_commands() -> tuple[list[str], list[str]]:
    """Return (copy_cmd, paste_cmd) for the current platform."""
    if sys.platform == "darwin":
        return (["pbcopy"], ["pbpaste"])
    if shutil.which("wl-copy"):
        return (["wl-copy"], ["wl-paste"])
    if shutil.which("xclip"):
        return (
            ["xclip", "-selection", "clipboard"],
            ["xclip", "-selection", "clipboard", "-o"],
        )
    if shutil.which("clip.exe"):  # WSL
        return (["clip.exe"], ["powershell.exe", "-command", "Get-Clipboard"])
    console.print("[red]Error:[/red] No clipboard command found (need pbcopy, xclip, wl-copy, or clip.exe)")
    raise typer.Exit(1)


def _copy_to_clipboard(content: str) -> None:
    """Copy content to the system clipboard."""
    copy_cmd, _ = _get_clipboard_commands()
    result = subprocess.run(copy_cmd, input=content, text=True, capture_output=True)
    if result.returncode != 0:
        console.print(f"[red]Error:[/red] {copy_cmd[0]} failed: {result.stderr.strip()}")
        raise typer.Exit(1)


def _save_temp_file(content: str) -> Path:
    """Save content to a timestamped temp file."""
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tmp_path = Path(f"/tmp/clipper-{timestamp}.txt")
    tmp_path.write_text(content)
    return tmp_path


# --- Domain commands ---


@app.command()
def copy(
    file: Annotated[
        Path | None,
        typer.Option("--file", "-f", help="Read content from a file instead of stdin"),
    ] = None,
):
    """Copy content to the system clipboard.

    Reads from --file or stdin, copies to clipboard, and saves a temp file for recovery.
    """
    if file is not None:
        if not file.exists():
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1)
        content = file.read_text()
    elif not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        console.print("[red]Error:[/red] No input. Provide --file or pipe content via stdin.")
        raise typer.Exit(1)

    if not content:
        console.print("[yellow]Warning:[/yellow] Empty content, nothing to copy.")
        raise typer.Exit(0)

    _copy_to_clipboard(content)
    tmp_path = _save_temp_file(content)

    byte_count = len(content.encode("utf-8"))
    preview = content.strip().replace("\n", " ")[:80]
    typer.echo(f"Copied {byte_count} bytes to clipboard")
    typer.echo(f'Preview: "{preview}"')
    typer.echo(f"Saved to {tmp_path}")


@app.command()
def paste():
    """Print clipboard contents to stdout."""
    _, paste_cmd = _get_clipboard_commands()
    result = subprocess.run(paste_cmd, text=True, capture_output=True)
    if result.returncode != 0:
        console.print(f"[red]Error:[/red] {paste_cmd[0]} failed: {result.stderr.strip()}")
        raise typer.Exit(1)
    typer.echo(result.stdout, nl=False)


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skill", "install", "clipper", "--from", str(skill_dir), "--yes"],
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
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
