# guppi-skills

Personal collection of CLI tools that double as AI agent skills. Each skill is a standalone Python CLI (installable via `uv tool install`) paired with a SKILL.md following the [Agent Skills](https://github.com/agent-skills/spec) open standard.

Skills work from the terminal for humans and from agents (Claude Code, Kiro, Copilot, etc.) via SKILL.md instructions.

## Project Workflow

### Tech Stack

- **Python 3.11+** — minimum version
- **Typer** — CLI framework (all skills use this)
- **Rich** — console output formatting (tables, panels, colors)
- **uv** — package manager and tool installer
- **hatchling** — build backend
- **pytest** — testing

### Library Preferences

Prefer the Python standard library over third-party packages. The guppi ecosystem is intentionally lean.

- **CLI:** Typer + Rich (already dependencies — use them freely)
- **TOML parsing:** `tomllib` (stdlib, Python 3.11+)
- **Paths:** `pathlib.Path` (not `os.path`)
- **Subprocesses:** `subprocess.run` (not `os.system`)
- **Type hints:** `typing.Annotated` for Typer args/options (stdlib, Python 3.9+)
- **Testing:** pytest + `typer.testing.CliRunner`
- **Tracking/storage:** `guppi-beads` (`lib/beads/`) for skills that need persistent metadata via beads
- **Avoid** adding new third-party dependencies unless clearly necessary

### Issue Tracking

Use beads (`bd`) for all task tracking. Do NOT use TodoWrite or markdown files for tracking.

```bash
bd ready                    # Find available work
bd show <id>                # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>               # Complete work
bd sync --flush-only        # Export to JSONL
```

### Development Commands

```bash
uv sync                     # Install dependencies (from skill directory)
uv run guppi-<name> --help  # Run skill locally
uv run pytest               # Run tests
guppi skills install <name> # Install skill globally via guppi CLI
```

### Releasing a Skill

Each skill is versioned and tagged independently. No repo-wide releases. See `RELEASE.md` for full details.

1. **Bump version** in 3 files: `<name>/pyproject.toml`, `<name>/src/guppi_<name>/__init__.py`, `<name>/SKILL.md`
2. **Commit**: `git commit -m "Bump <name> to X.Y.Z"`
3. **Tag**: `git tag -a <name>/vX.Y.Z -m "<name> version X.Y.Z"` — push tag
4. **Verify**: `guppi skills update <name> && guppi-<name> --help`

Tag format: `<name>/vX.Y.Z` (e.g., `spiker/v0.2.0`). Prompt for bump type if not specified.

---

## Skill Design Spec

### Directory Structure

Each skill lives in its own top-level directory:

```
<name>/
├── pyproject.toml          # Package metadata, entry points, build config
├── SKILL.md                # Agent Skills manifest (bundled into wheel)
├── README.md               # User guide (rendered by GitHub in directory views)
├── docs/
│   └── design/             # Feature design docs (iterate before implementing)
│       └── YYYY-MM-DD-slug.md
└── src/
    └── guppi_<name>/
        ├── __init__.py     # Version: __version__ = "0.1.0"
        ├── cli.py          # Typer app with commands + skill subcommand group
        └── ...             # Additional modules as needed
```

### Documentation Convention

Each skill has three layers of documentation, each for a different audience:

| File | Audience | Purpose |
|------|----------|---------|
| `README.md` | Human user | What it does, when/how to use it, example sessions |
| `SKILL.md` | AI agent | Instructions the agent follows when the skill is invoked |
| `docs/design/` | Developer | Architectural decisions, feature planning |

**README.md** is the user guide — written for the person invoking the skill. It should cover:
- What the skill does (plain language, not agent instructions)
- When to use it (example invocations)
- What to expect (what happens step by step, what decisions the user will make)
- Prerequisites and setup
- Example session showing a typical interaction
- CLI command reference (for direct terminal use)

GitHub renders README.md automatically when browsing a directory, so every skill's user guide is visible without extra clicks.

**SKILL.md** is for the agent — it tells the agent *how* to execute the skill. Users shouldn't need to read this to use the skill.

### Design Docs

Each skill has a `docs/design/` directory for planning features before implementation.

**Workflow:**
1. Create a design doc in `<name>/docs/design/YYYY-MM-DD-slug.md`
2. Iterate on the design with the user
3. Once the design is agreed upon, create beads issues to plan and track implementation

**Naming:** `YYYY-MM-DD-slug.md` (e.g., `2026-02-12-caching-layer.md`)

### Naming Conventions

Skill names should be **pithy, short "-er" verbs** that describe what the skill does (e.g., `spiker`, `snapper`, `clipper`, `courier`). Think action words, not nouns.

| Thing | Convention | Example |
|-------|-----------|---------|
| Directory | `<name>` | `spiker` |
| Package name | `guppi-<name>` | `guppi-spiker` |
| Python package | `guppi_<name>` | `guppi_spiker` |
| CLI command | `guppi-<name>` | `guppi-spiker` |
| Typer app var | `app` | `app = typer.Typer(...)` |
| `[tool.guppi] name` | `<name>` | `spiker` |
| Config | `~/.config/guppi/<name>/` | Settings, preferences |
| Data | `~/.local/share/guppi/<name>/` | Important, portable user data |
| State | `~/.local/state/guppi/<name>/` | Cursors, offsets, history |
| Cache | `~/.cache/guppi/<name>/` | Non-essential, regenerable |

Skills use [XDG Base Directory](https://specifications.freedesktop.org/basedir/latest/) conventions. Config files use JSON (`config.json`). Not every skill needs all four directories — only create what you use.

### pyproject.toml Template

```toml
[project]
name = "guppi-<name>"
version = "0.1.0"
description = "<one-line description>"
requires-python = ">=3.11"
dependencies = [
    "typer>=0.9.0",
]

[project.scripts]
guppi-<name> = "guppi_<name>.cli:app"

[tool.guppi]
name = "<name>"
description = "<one-line description>"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/guppi_<name>"]

[tool.hatch.build.targets.wheel.force-include]
"SKILL.md" = "guppi_<name>/SKILL.md"
```

The `force-include` section bundles SKILL.md into the wheel so it's available at runtime for the `skill show` command and agent discovery after `uv tool install`.

### SKILL.md Format

SKILL.md follows the Agent Skills open standard: YAML frontmatter + markdown body.

```markdown
---
name: <name>
description: >
  <one-line description of what this skill does and when to use it>
allowed-tools: "Bash(guppi-<name>:*)"
version: "0.1.0"
author: "<author name>"
license: "MIT"
---

# <Name> — <tagline>

<paragraph explaining the skill's purpose and when an agent should use it>

## Commands

### `guppi-<name> <command> [args]`

<description of command>

**Arguments:**
- `arg` — description

**Options:**
- `--option` / `-o` — description

## Examples

```bash
guppi-<name> <command> example-arg
```

## Skill Management

```bash
guppi-<name> skill install   # Register with guppi-cli
guppi-<name> skill show      # Display SKILL.md contents
```
```

### JSON Output Convention (`--json`)

Commands that output structured data (tables, lists, status info) **must** support a `--json` flag. This makes skill output machine-readable for agents and scriptable for humans.

**Rules:**
- Flag: `json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False`
- Output: `json.dumps(data, indent=2)` via `typer.echo()`, then return early (before table rendering)
- Data: list of dicts for collections, single dict for status/info commands
- Default: human-readable table output remains the default (no `--json` = table)
- Import: `import json` inline (only when `--json` is used)

**Pattern:**
```python
@app.command()
def list_things(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """List things."""
    items = _get_items()  # build your data as list of dicts

    if json_output:
        import json
        typer.echo(json.dumps(items, indent=2))
        return

    # ... table rendering below ...
```

**Which commands need `--json`:** any command that renders a table or structured list. Not needed for: single-value lookups (e.g., `locker get`), interactive commands (e.g., `tracker review`), or action commands (e.g., `install`, `init`).

### CLI Pattern (cli.py)

Every skill has a Typer app with:
1. **`--version` / `-V` flag** — standard version callback (eager, prints `guppi-<name> X.Y.Z`)
2. **`init` command** (optional) — one-time per-machine setup (hooks, config files, etc.). Idempotent — safe to run multiple times. Not every skill needs this.
3. **Domain commands** — the actual skill functionality (with `--json` on structured output commands)
4. **`skill` subcommand group** — standard install/show commands for agent discovery

```python
"""GUPPI <name> skill CLI"""

import typer
from typing import Annotated

from guppi_<name> import __version__


def _version_callback(value: bool):
    if value:
        typer.echo(f"guppi-<name> {__version__}")
        raise typer.Exit()


app = typer.Typer(help="<one-line description>")


@app.callback()
def main(
    version: Annotated[bool, typer.Option("--version", "-V", help="Show version and exit", callback=_version_callback, is_eager=True)] = False,
):
    pass

# --- Init (optional — only if skill needs per-machine setup) ---

@app.command()
def init():
    """One-time per-machine setup (hooks, config, etc.)."""
    typer.echo("Initialized <name>.")

# --- Domain commands ---

@app.command()
def main_command(
    arg: Annotated[str, typer.Argument(help="Description")],
    option: Annotated[bool, typer.Option("--option", "-o", help="Description")] = False,
):
    """Command description"""
    # implementation
    pass

# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")

@skill_app.command()
def install():
    """Register this skill with guppi-cli"""
    import subprocess
    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skills", "install", "<name>", "--from", str(skill_dir), "--yes"],
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
    from pathlib import Path
    # When installed via uv tool install, SKILL.md is in the package directory
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
```

### __init__.py Template

```python
"""GUPPI <name> skill"""

__version__ = "0.1.0"
```

### Installation Workflow

**Prefer guppi CLI** for installing and updating skills. It handles both `uv tool install` and SKILL.md registration in one step.

1. **guppi CLI** (preferred) — install and register in one step:
   ```bash
   guppi skills install <name>                        # Install from sources
   guppi skills install <name> --source guppi-skills  # Install from specific source
   guppi skills install <name> --from <path>          # Install from local path
   ```

2. **Per-skill command** — register an already-installed skill:
   ```bash
   guppi-<name> skill install
   ```

3. **uv direct** — install without guppi registration (dev only):
   ```bash
   cd <name>/
   uv tool install .
   ```

### Updating Skills

Use guppi CLI to update sources and skills. Do NOT use `uv tool upgrade` directly.

```bash
# Update sources (git pull latest from registered repos)
guppi skills source update                # Update all sources
guppi skills source update guppi-skills   # Update specific source

# Update installed skills (reinstalls from source)
guppi skills update              # Update all installed guppi-* skills
guppi skills update <name>       # Update specific skill
```

**Typical update workflow** after pushing changes to a skill:
```bash
guppi skills source update    # Pull latest source
guppi skills update <name>    # Reinstall skill from updated source
```

### Validating a New Skill

After creating a skill, verify end-to-end:

```bash
# 1. Install via guppi CLI
guppi skills install <name> --from ./<name>

# 2. Run the CLI
guppi-<name> --help
guppi-<name> <main-command> <test-args>

# 3. Run init if the skill has one
guppi-<name> init              # One-time per-machine setup (idempotent)

# 4. Verify skill management
guppi-<name> skill show        # Should print SKILL.md contents

# 5. Run tests
cd <name>/
uv run pytest

# 6. Clean up (optional)
guppi skills uninstall <name>
```

---

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds
