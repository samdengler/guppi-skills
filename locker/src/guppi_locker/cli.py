"""GUPPI locker skill CLI"""

import subprocess
from pathlib import Path
from typing import Annotated

import typer

from guppi_locker import __version__, vault


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-locker {__version__}")
        raise typer.Exit()


app = typer.Typer(help="Deterministic secret storage for guppi skills", pretty_exceptions_enable=False)


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass


def _require_init():
    """Exit with error if locker hasn't been initialized."""
    if not vault.is_initialized():
        typer.echo("Error: Locker not initialized. Run 'guppi-locker init' to get started.", err=True)
        raise typer.Exit(1)


# --- Setup commands ---


@app.command()
def init(
    force: Annotated[bool, typer.Option("--force", help="Regenerate master key (destroys existing secrets)")] = False,
):
    """Initialize locker — generate master key and create encrypted secrets file."""
    if vault.is_initialized() and not force:
        typer.echo("Locker is already initialized.")
        return

    if vault.is_initialized() and force:
        confirm = typer.confirm("This will destroy all existing secrets. Continue?", default=False)
        if not confirm:
            raise typer.Exit()

    typer.echo("Generating master key... ", nl=False)
    vault.initialize(force=force)
    typer.echo("done.")
    typer.echo(f"Secrets file: {vault.SECRETS_FILE}")


# --- Secret commands ---


@app.command()
def get(
    service: Annotated[str, typer.Argument(help="Service name (e.g., courier)")],
    key: Annotated[str, typer.Argument(help="Secret key name (e.g., handoffs)")],
):
    """Retrieve a secret. Prints the value to stdout."""
    _require_init()
    try:
        value = vault.get(service, key)
    except vault.SecretNotFoundError:
        typer.echo(f"Error: Secret '{service}/{key}' not found.", err=True)
        raise typer.Exit(1)
    typer.echo(value, nl=False)


@app.command("set")
def set_cmd(
    service: Annotated[str, typer.Argument(help="Service name (e.g., courier)")],
    key: Annotated[str, typer.Argument(help="Secret key name (e.g., handoffs)")],
    value: Annotated[str | None, typer.Option("--value", help="Secret value (prompts if omitted)")] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite without confirmation")] = False,
):
    """Store a secret."""
    _require_init()

    if value is None:
        value = typer.prompt("Value", hide_input=True)

    try:
        vault.set(service, key, value)
    except vault.SecretExistsError:
        if not force:
            overwrite = typer.confirm(f"Secret '{service}/{key}' already exists. Overwrite?", default=False)
            if not overwrite:
                raise typer.Exit()
        vault.update(service, key, value)

    typer.echo(f"Stored '{service}/{key}'.", err=True)


@app.command()
def delete(
    service: Annotated[str, typer.Argument(help="Service name (e.g., courier)")],
    key: Annotated[str, typer.Argument(help="Secret key name (e.g., handoffs)")],
):
    """Delete a secret."""
    _require_init()
    try:
        vault.delete(service, key)
    except vault.SecretNotFoundError:
        typer.echo(f"Error: Secret '{service}/{key}' not found.", err=True)
        raise typer.Exit(1)
    typer.echo(f"Deleted '{service}/{key}'.", err=True)


@app.command("list")
def list_cmd(
    service: Annotated[str | None, typer.Argument(help="Filter by service name")] = None,
):
    """List secrets. Never prints secret values."""
    _require_init()
    secrets = vault.list_secrets(service)

    if not secrets:
        if service:
            typer.echo(f"No secrets found for service '{service}'.")
        else:
            typer.echo("No secrets found.")
        return

    if service:
        for _, key in secrets:
            typer.echo(f"  {key}")
    else:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(show_header=True, header_style="bold")
        table.add_column("Service")
        table.add_column("Key")
        for svc, key in secrets:
            table.add_row(svc, key)
        console.print(table)


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "locker", "--from", str(skill_dir), "--yes"],
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
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
