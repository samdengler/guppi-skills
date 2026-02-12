# guppi-skills

Personal collection of CLI tools that double as AI agent skills. Each skill is a standalone Python CLI (installable via `uv tool install`) paired with a SKILL.md following the [Agent Skills](https://github.com/agent-skills/spec) open standard.

Skills work from the terminal for humans and from agents (Claude Code, Copilot, etc.) via SKILL.md instructions.

## Project Workflow

### Tech Stack

- **Python 3.11+** — minimum version
- **Typer** — CLI framework
- **uv** — package manager and tool installer
- **hatchling** — build backend
- **pytest** — testing

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
uv tool install .           # Install skill globally (from skill directory)
```

---

## Skill Design Spec

### Directory Structure

Each skill lives in its own top-level directory:

```
<name>/
├── pyproject.toml          # Package metadata, entry points, build config
├── SKILL.md                # Agent Skills manifest (bundled into wheel)
├── docs/
│   └── design/             # Feature design docs (iterate before implementing)
│       └── YYYY-MM-DD-slug.md
└── src/
    └── guppi_<name>/
        ├── __init__.py     # Version: __version__ = "0.1.0"
        ├── cli.py          # Typer app with commands + skill subcommand group
        └── ...             # Additional modules as needed
```

### Design Docs

Each skill has a `docs/design/` directory for planning features before implementation.

**Workflow:**
1. Create a design doc in `<name>/docs/design/YYYY-MM-DD-slug.md`
2. Iterate on the design with the user
3. Once the design is agreed upon, create beads issues to plan and track implementation

**Naming:** `YYYY-MM-DD-slug.md` (e.g., `2026-02-12-caching-layer.md`)

### Naming Conventions

| Thing | Convention | Example |
|-------|-----------|---------|
| Directory | `<name>` | `spiker` |
| Package name | `guppi-<name>` | `guppi-spiker` |
| Python package | `guppi_<name>` | `guppi_spiker` |
| CLI command | `guppi-<name>` | `guppi-spiker` |
| Typer app var | `app` | `app = typer.Typer(...)` |
| `[tool.guppi] name` | `<name>` | `spiker` |

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

### CLI Pattern (cli.py)

Every skill has a Typer app with:
1. **Domain commands** — the actual skill functionality
2. **`skill` subcommand group** — standard install/show commands for agent discovery

```python
"""GUPPI <name> skill CLI"""

import typer
from typing_extensions import Annotated

app = typer.Typer(help="<one-line description>")

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
    import sys
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

Skills can be installed three ways:

1. **uv direct** — install from the repo:
   ```bash
   cd <name>/
   uv tool install .
   ```

2. **guppi-cli** — register for agent discovery:
   ```bash
   guppi-<name> skill install
   ```

3. **uvx ephemeral** — run without installing:
   ```bash
   uvx --from ./path/to/<name> guppi-<name> <command>
   ```

### Validating a New Skill

After creating a skill, verify end-to-end:

```bash
# 1. Build and install
cd <name>/
uv tool install .

# 2. Run the CLI
guppi-<name> --help
guppi-<name> <main-command> <test-args>

# 3. Verify skill management
guppi-<name> skill show        # Should print SKILL.md contents
guppi-<name> skill install     # Should register with guppi-cli

# 4. Run tests
uv run pytest

# 5. Clean up (optional)
uv tool uninstall guppi-<name>
```
