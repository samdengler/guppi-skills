"""GUPPI dotfiles skill CLI"""

import json
import os
import re
import shutil
import subprocess
import tomllib
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from guppi_dotfiles import __version__


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-dotfiles {__version__}")
        raise typer.Exit()


app = typer.Typer(
    help="Add, remove, and reconcile machine dependencies through the dotfiles manifests (Brewfile and mise config)"
)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True),
    ] = False,
):
    pass


console = Console()


class Via(str, Enum):
    mise = "mise"
    brew = "brew"
    cask = "cask"


# Backend prefixes that only mise understands. Anything with one of these goes to mise without a lookup.
MISE_PREFIXES = (
    "npm:", "pipx:", "cargo:", "go:", "ubi:", "aqua:", "asdf:", "core:",
    "github:", "gitlab:", "gem:", "spm:", "vfox:", "dotnet:", "http:",
)

BREWFILE_ENTRY = re.compile(r'^\s*(brew|cask|mas|tap)\s+"([^"]+)"')


# --- Paths and config ---


def _dotfiles_root() -> Path:
    return Path(os.environ.get("DOTFILES_PATH", Path.home() / ".dotfiles"))


def _brewfile() -> Path:
    return _dotfiles_root() / "Brewfile"


def _mise_config() -> Path:
    """The mise global config. mise honors MISE_GLOBAL_CONFIG_FILE, so the same value works for subprocesses."""
    if env := os.environ.get("MISE_GLOBAL_CONFIG_FILE"):
        return Path(env)
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return xdg / "mise" / "config.toml"


def _config_path() -> Path:
    xdg = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return xdg / "guppi" / "dotfiles" / "config.json"


def _load_config() -> dict:
    path = _config_path()
    if not path.exists():
        return {"ignore": []}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"ignore": []}
    data.setdefault("ignore", [])
    return data


def _save_config(data: dict) -> None:
    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


# --- Subprocess helpers ---


def _run(cmd: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    env = os.environ | {"HOMEBREW_NO_AUTO_UPDATE": "1", "HOMEBREW_NO_ENV_HINTS": "1"}
    return subprocess.run(cmd, check=check, capture_output=capture, text=True, env=env)


def _require(tool: str) -> None:
    if shutil.which(tool) is None:
        console.print(f"[red]Error:[/red] {tool} is not installed or not on PATH")
        raise typer.Exit(1)


def _fail(message: str) -> None:
    console.print(f"[red]Error:[/red] {message}")
    raise typer.Exit(1)


def _short(name: str) -> str:
    """Last path segment of a possibly tap-qualified brew name."""
    return name.rsplit("/", 1)[-1]


def _mise_tool(spec: str) -> str:
    """Tool name without the version suffix. Brew names can contain @ (postgresql@16), mise specs use @ for versions."""
    return spec.split("@", 1)[0]


# --- Manifest readers ---


def _brewfile_entries(kind: str) -> list[str]:
    path = _brewfile()
    if not path.exists():
        return []
    entries = []
    for line in path.read_text().splitlines():
        if match := BREWFILE_ENTRY.match(line):
            if match.group(1) == kind:
                entries.append(match.group(2))
    return entries


def _mise_entries() -> list[str]:
    path = _mise_config()
    if not path.exists():
        return []
    with path.open("rb") as f:
        data = tomllib.load(f)
    return list(data.get("tools", {}).keys())


def _manifest() -> dict[str, list[str]]:
    return {
        "mise": _mise_entries(),
        "brew": _brewfile_entries("brew"),
        "cask": _brewfile_entries("cask"),
    }


def _find_in_manifest(name: str) -> Via | None:
    manifest = _manifest()
    if name in manifest["mise"] or _mise_tool(name) in manifest["mise"]:
        return Via.mise
    if any(_short(entry) == _short(name) for entry in manifest["brew"]):
        return Via.brew
    if name in manifest["cask"]:
        return Via.cask
    return None


# --- Installed-state readers ---


def _lines(result: subprocess.CompletedProcess) -> list[str]:
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _brew_leaves() -> list[str]:
    return _lines(_run(["brew", "leaves", "--installed-on-request"]))


def _brew_formulae_installed() -> list[str]:
    return _lines(_run(["brew", "list", "--formula"]))


def _brew_casks_installed() -> list[str]:
    return _lines(_run(["brew", "list", "--cask"]))


def _mise_installed() -> dict[str, list[dict]]:
    result = _run(["mise", "ls", "--json", "--installed"])
    return json.loads(result.stdout or "{}")


def _mise_missing() -> list[str]:
    result = _run(["mise", "ls", "--json", "--missing"])
    return list(json.loads(result.stdout or "{}").keys())


# --- Routing ---


def _mise_knows(tool: str) -> bool:
    if tool.startswith(MISE_PREFIXES):
        return True
    result = _run(["mise", "registry", tool], check=False)
    return result.returncode == 0 and bool(result.stdout.strip())


def _brew_kind(name: str) -> Via | None:
    result = _run(["brew", "info", "--json=v2", name], check=False)
    if result.returncode != 0:
        return None
    try:
        info = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if info.get("casks"):
        return Via.cask
    if info.get("formulae"):
        return Via.brew
    return None


def _route(pkg: str, via: Via | None) -> Via:
    """Pick a backend. mise wins when it can install the tool; brew and casks are the fallback."""
    if via is not None:
        return via
    if _mise_knows(_mise_tool(pkg)):
        return Via.mise
    kind = _brew_kind(pkg)
    if kind is None:
        _fail(f"'{pkg}' was not found in the mise registry or in Homebrew. Pass --via to force a backend.")
    return kind


# --- Install/remove primitives ---


def _install(pkg: str, via: Via) -> None:
    """Install a package and record it in the matching manifest."""
    if via is Via.mise:
        _run(["mise", "use", "--global", "--yes", pkg], capture=False)
        return
    brewfile = str(_brewfile())
    if via is Via.cask:
        _run(["brew", "install", "--cask", pkg], capture=False)
        _run(["brew", "bundle", "add", "--file", brewfile, "--cask", pkg], capture=False)
    else:
        _run(["brew", "install", pkg], capture=False)
        _run(["brew", "bundle", "add", "--file", brewfile, pkg], capture=False)


def _uninstall(pkg: str, via: Via, keep: bool) -> None:
    """Remove a package from its manifest, and from the machine unless keep is set."""
    if via is Via.mise:
        cmd = ["mise", "unuse", "--global", pkg]
        if keep:
            cmd.append("--no-prune")
        _run(cmd, capture=False)
        return
    brewfile = str(_brewfile())
    type_flag = "--cask" if via is Via.cask else "--formula"
    _run(["brew", "bundle", "remove", "--file", brewfile, type_flag, pkg], capture=False)
    if not keep:
        _run(["brew", "uninstall", type_flag, pkg], capture=False)


# --- Commands ---


@app.command()
def add(
    packages: Annotated[list[str], typer.Argument(help="Package names (mise spec like node@24, brew formula, or cask)")],
    via: Annotated[Via | None, typer.Option("--via", help="Force a backend instead of auto-routing")] = None,
):
    """Install packages and record them in the dotfiles manifests.

    Routing prefers mise. A package goes to Homebrew only when mise cannot install it,
    and to a cask when Homebrew knows it only as a cask.
    """
    _require("brew")
    _require("mise")
    for pkg in packages:
        existing = _find_in_manifest(pkg)
        if existing is not None:
            console.print(f"[yellow]Skipped[/yellow] {pkg}: already in the {existing.value} manifest")
            continue
        target = _route(pkg, via)
        console.print(f"[cyan]Adding[/cyan] {pkg} via {target.value}")
        _install(pkg, target)
        console.print(f"[green]Added[/green] {pkg} ({target.value})")
    console.print(f"Commit the manifest change in {_dotfiles_root()}")


@app.command()
def remove(
    packages: Annotated[list[str], typer.Argument(help="Package names as they appear in the manifests")],
    keep: Annotated[bool, typer.Option("--keep", help="Drop from the manifest but leave it installed")] = False,
):
    """Remove packages from the dotfiles manifests and uninstall them."""
    _require("brew")
    _require("mise")
    for pkg in packages:
        via = _find_in_manifest(pkg)
        if via is None:
            console.print(f"[yellow]Skipped[/yellow] {pkg}: not in any manifest")
            continue
        console.print(f"[cyan]Removing[/cyan] {pkg} from {via.value}")
        _uninstall(pkg, via, keep)
        console.print(f"[green]Removed[/green] {pkg} ({via.value})")
    console.print(f"Commit the manifest change in {_dotfiles_root()}")


@app.command("list")
def list_packages(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List every package recorded in the manifests."""
    manifest = _manifest()
    rows = [{"name": name, "via": via} for via in ("mise", "brew", "cask") for name in manifest[via]]

    if json_output:
        typer.echo(json.dumps(rows, indent=2))
        return

    table = Table(title=f"Manifests in {_dotfiles_root()}")
    table.add_column("Via", style="cyan")
    table.add_column("Package")
    for row in rows:
        table.add_row(row["via"], row["name"])
    console.print(table)


def _compute_drift() -> dict[str, list[dict]]:
    """Compare installed packages against the manifests.

    extra: installed on this machine but absent from every manifest.
    missing: in a manifest but not installed here.
    """
    manifest = _manifest()
    ignore = set(_load_config()["ignore"])

    brew_manifest_short = {_short(name) for name in manifest["brew"]}
    cask_manifest = set(manifest["cask"])
    mise_manifest = set(manifest["mise"])

    extra: list[dict] = []
    for name in _brew_leaves():
        if _short(name) not in brew_manifest_short and _short(name) not in ignore and name not in ignore:
            extra.append({"name": name, "via": "brew"})
    for name in _brew_casks_installed():
        if name not in cask_manifest and name not in ignore:
            extra.append({"name": name, "via": "cask"})
    for tool, versions in _mise_installed().items():
        if tool in mise_manifest or tool in ignore:
            continue
        if all(not entry.get("source") for entry in versions):
            extra.append({"name": tool, "via": "mise"})

    missing: list[dict] = []
    installed_formulae = {_short(name) for name in _brew_formulae_installed()}
    for name in manifest["brew"]:
        if _short(name) not in installed_formulae:
            missing.append({"name": name, "via": "brew"})
    installed_casks = set(_brew_casks_installed())
    for name in manifest["cask"]:
        if name not in installed_casks:
            missing.append({"name": name, "via": "cask"})
    for tool in _mise_missing():
        if tool in mise_manifest:
            missing.append({"name": tool, "via": "mise"})

    return {"extra": extra, "missing": missing}


@app.command()
def drift(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    fix: Annotated[bool, typer.Option("--fix", help="Adopt extras into the manifests and install missing ones")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="With --fix, print the plan without running it")] = False,
    via: Annotated[Via | None, typer.Option("--via", help="With --fix, force a backend for adopted extras")] = None,
):
    """Show packages installed outside the manifests, and manifest entries not installed.

    With --fix, each extra is re-added through normal routing. A brew formula that mise
    can install is recorded under mise; the brew copy is left in place and reported.
    """
    _require("brew")
    _require("mise")
    result = _compute_drift()

    if json_output and not fix:
        typer.echo(json.dumps(result, indent=2))
        return

    if not fix:
        _print_drift(result)
        return

    plan = []
    for item in result["extra"]:
        target = _route(item["name"], via)
        plan.append({"name": item["name"], "from": item["via"], "to": target.value})

    if dry_run:
        if json_output:
            typer.echo(json.dumps({"plan": plan, "missing": result["missing"]}, indent=2))
            return
        table = Table(title="Fix plan")
        table.add_column("Package")
        table.add_column("Installed via", style="yellow")
        table.add_column("Record under", style="cyan")
        for step in plan:
            table.add_row(step["name"], step["from"], step["to"])
        console.print(table)
        if result["missing"]:
            console.print(f"{len(result['missing'])} missing package(s) would be installed by sync")
        return

    rehomed = []
    for step in plan:
        console.print(f"[cyan]Adopting[/cyan] {step['name']} via {step['to']}")
        _install(step["name"], Via(step["to"]))
        if step["from"] != step["to"]:
            rehomed.append(step)
    if result["missing"]:
        console.print("[cyan]Installing[/cyan] missing manifest entries")
        _sync()
    for step in rehomed:
        flag = " --cask" if step["from"] == "cask" else ""
        console.print(
            f"[yellow]Note[/yellow] {step['name']} is now managed by {step['to']}; "
            f"the {step['from']} copy is still installed. Remove it with: brew uninstall{flag} {step['name']}"
        )
    console.print(f"Commit the manifest change in {_dotfiles_root()}")


def _print_drift(result: dict[str, list[dict]]) -> None:
    if not result["extra"] and not result["missing"]:
        console.print("[green]No drift.[/green] Installed packages match the manifests.")
        return
    if result["extra"]:
        table = Table(title="Installed but not in a manifest")
        table.add_column("Via", style="yellow")
        table.add_column("Package")
        for item in result["extra"]:
            table.add_row(item["via"], item["name"])
        console.print(table)
    if result["missing"]:
        table = Table(title="In a manifest but not installed")
        table.add_column("Via", style="yellow")
        table.add_column("Package")
        for item in result["missing"]:
            table.add_row(item["via"], item["name"])
        console.print(table)
    console.print("Run [bold]guppi-dotfiles drift --fix[/bold] to adopt extras, or [bold]sync[/bold] to install missing ones.")


def _sync() -> None:
    _run(["brew", "bundle", "install", "--file", str(_brewfile()), "--no-upgrade"], capture=False)
    _run(["mise", "install", "--yes"], capture=False)


@app.command()
def sync():
    """Install everything in the manifests that is not yet installed. Does not upgrade."""
    _require("brew")
    _require("mise")
    _sync()
    console.print("[green]Synced[/green] manifests to this machine")


@app.command()
def ignore(
    names: Annotated[list[str] | None, typer.Argument(help="Package names drift should stop reporting")] = None,
    remove_names: Annotated[bool, typer.Option("--remove", help="Stop ignoring the given names")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """Manage the list of packages that drift ignores. With no names, show the list."""
    config = _load_config()
    current = list(config["ignore"])
    if names:
        if remove_names:
            current = [name for name in current if name not in names]
        else:
            current = sorted(set(current) | set(names))
        config["ignore"] = current
        _save_config(config)

    if json_output:
        typer.echo(json.dumps(current, indent=2))
        return
    if not current:
        console.print("No ignored packages")
        return
    for name in current:
        typer.echo(name)


# --- Skill management ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli."""
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "dotfiles", "--from", str(skill_dir), "--yes"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        console.print(f"[red]Error:[/red] {result.stderr.strip()}")
        raise typer.Exit(1)
    console.print("[green]Registered[/green] dotfiles skill with guppi-cli")


@skill_app.command()
def show():
    """Display SKILL.md contents."""
    typer.echo(_get_skill_md_path().read_text())


def _get_skill_md_path() -> Path:
    package_dir = Path(__file__).parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        console.print("[red]Error:[/red] SKILL.md not found")
        raise typer.Exit(1)
    return skill_md
