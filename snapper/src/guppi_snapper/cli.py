"""GUPPI snapper skill CLI"""

import subprocess
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(help="CDP browser screenshots for capturing authenticated web pages")


# --- Domain commands ---


@app.command()
def init():
    """Set up snapper: install Chromium and create directory structure."""
    from rich.console import Console

    from guppi_snapper.browser import find_chromium_binary, install_chromium
    from guppi_snapper.paths import data_dir, extensions_dir, profiles_dir

    console = Console()

    # Create directory structure
    for d in [profiles_dir(), extensions_dir()]:
        d.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓[/green] Data directory: {data_dir()}")

    # Install Chromium if needed
    chromium = find_chromium_binary()
    if chromium:
        console.print(f"[green]✓[/green] Chromium already installed: {chromium}")
    else:
        console.print("Installing Playwright Chromium...")
        if install_chromium():
            chromium = find_chromium_binary()
            console.print(f"[green]✓[/green] Chromium installed: {chromium}")
        else:
            console.print("[red]✗[/red] Failed to install Chromium", style="bold red")
            raise typer.Exit(1)

    console.print("\n[bold green]Snapper is ready![/bold green] Run [bold]guppi-snapper start[/bold] to launch Chromium.")


@app.command()
def start(
    profile: Annotated[str, typer.Option("--profile", "-p", help="Profile name")] = "default",
    port: Annotated[int, typer.Option(help="CDP port")] = 9222,
):
    """Launch Chromium with CDP enabled using a named profile."""
    from guppi_snapper.browser import (
        find_chromium_binary,
        is_port_in_use,
        launch_chromium,
        save_state,
    )
    from guppi_snapper.paths import extensions_dir, profile_path

    if is_port_in_use(port):
        typer.echo(f"Error: port {port} is already in use", err=True)
        raise typer.Exit(1)

    chromium = find_chromium_binary()
    if not chromium:
        typer.echo("Error: Chromium is not installed. Run 'guppi-snapper init' first.", err=True)
        raise typer.Exit(1)

    prof_dir = profile_path(profile)
    prof_dir.mkdir(parents=True, exist_ok=True)

    # Discover extensions
    ext_dir = extensions_dir()
    extensions: list[Path] = []
    if ext_dir.is_dir():
        extensions = [
            d for d in ext_dir.iterdir()
            if d.is_dir() and (d / "manifest.json").exists()
        ]

    pid = launch_chromium(chromium, port, prof_dir, extensions)
    save_state(pid, port, profile)

    typer.echo(f"Chromium started (pid={pid}, port={port}, profile={profile})")
    if extensions:
        typer.echo(f"Extensions loaded: {', '.join(e.name for e in extensions)}")


@app.command()
def status(
    port: Annotated[int, typer.Option(help="CDP port")] = 9222,
):
    """Check if Chromium is running with CDP and show connection info."""
    from guppi_snapper.browser import get_cdp_info, list_tabs, load_state

    state = load_state()
    if not state:
        typer.echo("No running Chromium instance found")
        raise typer.Exit(1)

    info = get_cdp_info(state["port"])
    if not info:
        typer.echo("Chromium state file exists but CDP is not responding")
        raise typer.Exit(1)

    typer.echo(f"Chromium CDP active on port {state['port']}")
    typer.echo(f"Profile: {state['profile']}")
    typer.echo(f"PID: {state['pid']}")
    typer.echo(f"Browser: {info.get('Browser', 'unknown')}")

    tabs = list_tabs(state["port"])
    if tabs:
        typer.echo(f"Tabs: {len(tabs)}")
        for tab in tabs[:10]:
            typer.echo(f"  - {tab.get('title', 'untitled')} ({tab.get('url', '')})")


@app.command()
def stop():
    """Gracefully shut down the CDP Chromium instance."""
    from guppi_snapper.browser import load_state, stop_chromium
    from guppi_snapper.paths import state_file

    state = load_state()
    if not state:
        typer.echo("No running Chromium instance found")
        raise typer.Exit(1)

    stop_chromium(state["pid"], state_file())
    typer.echo("Chromium stopped")


@app.command()
def capture(
    url: Annotated[str, typer.Argument(help="URL to capture (or URL pattern with --existing)")],
    output: Annotated[str, typer.Option("--output", "-o", help="Output file path")] = "screenshot.png",
    viewport: Annotated[str, typer.Option("--viewport", "-v", help="Viewport dimensions (WxH)")] = "1400x1365",
    resize: Annotated[str | None, typer.Option("--resize", "-r", help="Resize to WxH after capture")] = None,
    wait: Annotated[int, typer.Option("--wait", "-w", help="Seconds to wait after load")] = 5,
    existing: Annotated[bool, typer.Option("--existing", "-e", help="Capture an already-open tab matching URL pattern")] = False,
    port: Annotated[int, typer.Option(help="CDP port")] = 9222,
):
    """Navigate to a URL and capture a screenshot."""
    from guppi_snapper.capture import parse_viewport, take_screenshot

    width, height = parse_viewport(viewport)
    resize_dims = parse_viewport(resize) if resize else None
    take_screenshot(port, url, output, width, height, wait, existing=existing, resize=resize_dims)
    typer.echo(f"Screenshot saved to {output}")


@app.command()
def batch(
    config_file: Annotated[Path, typer.Argument(help="Path to YAML config file")],
    port: Annotated[int, typer.Option(help="CDP port")] = 9222,
):
    """Capture multiple screenshots from a YAML config file."""
    from rich.console import Console
    from rich.progress import Progress

    from guppi_snapper.batch import load_batch_config, resolve_capture
    from guppi_snapper.capture import parse_viewport, take_screenshot

    console = Console()
    config = load_batch_config(config_file)
    captures = config["captures"]
    defaults = {
        "viewport": config.get("viewport", "1400x1365"),
        "wait": config.get("wait", 5),
        "output_dir": config.get("output_dir", "."),
        "resize": config.get("resize"),
        "existing": config.get("existing", False),
    }

    with Progress(console=console) as progress:
        task = progress.add_task("Capturing screenshots...", total=len(captures))
        for cap in captures:
            resolved = resolve_capture(cap, defaults)
            width, height = parse_viewport(resolved["viewport"])
            output_path = str(Path(resolved["output_dir"]) / resolved["output"])
            resize_dims = parse_viewport(resolved["resize"]) if resolved.get("resize") else None
            take_screenshot(
                port, resolved["url"], output_path, width, height,
                resolved["wait"], existing=resolved["existing"], resize=resize_dims,
            )
            console.print(f"  [green]✓[/green] {resolved['output']}")
            progress.advance(task)

    console.print(f"\n[bold green]Captured {len(captures)} screenshots[/bold green]")


# --- Profile subcommand group ---

profile_app = typer.Typer(help="Manage browser profiles")
app.add_typer(profile_app, name="profile")


@profile_app.command("list")
def profile_list():
    """List available profiles."""
    from rich.console import Console
    from rich.table import Table

    from guppi_snapper.paths import profiles_dir

    console = Console()
    pdir = profiles_dir()
    if not pdir.is_dir():
        console.print("No profiles found")
        raise typer.Exit()

    profiles = sorted(d for d in pdir.iterdir() if d.is_dir())
    if not profiles:
        console.print("No profiles found")
        raise typer.Exit()

    table = Table(title="Browser Profiles")
    table.add_column("Name")
    table.add_column("Last Modified")
    table.add_column("Size")

    for p in profiles:
        stat = p.stat()
        from datetime import datetime
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        # Rough size calculation
        size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        if size > 1_000_000:
            size_str = f"{size / 1_000_000:.1f} MB"
        elif size > 1_000:
            size_str = f"{size / 1_000:.1f} KB"
        else:
            size_str = f"{size} B"
        table.add_row(p.name, mtime, size_str)

    console.print(table)


@profile_app.command()
def create(
    name: Annotated[str, typer.Argument(help="Profile name")],
):
    """Create a new empty profile directory."""
    from guppi_snapper.paths import profile_path

    path = profile_path(name)
    if path.exists():
        typer.echo(f"Profile '{name}' already exists")
        raise typer.Exit(1)
    path.mkdir(parents=True)
    typer.echo(f"Created profile: {name}")


@profile_app.command()
def delete(
    name: Annotated[str, typer.Argument(help="Profile name")],
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation")] = False,
):
    """Delete a profile directory."""
    import shutil

    from guppi_snapper.paths import profile_path

    path = profile_path(name)
    if not path.exists():
        typer.echo(f"Profile '{name}' not found")
        raise typer.Exit(1)

    if not yes:
        confirm = typer.confirm(f"Delete profile '{name}'?")
        if not confirm:
            raise typer.Exit()

    shutil.rmtree(path)
    typer.echo(f"Deleted profile: {name}")


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skill", "install", "snapper", "--from", str(skill_dir), "--yes"],
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
