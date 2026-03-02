# Shared Beads Integration Library (guppi-beads)

**Date:** 2026-03-02
**Status:** Design

## Motivation

Multiple guppi skills need lightweight persistent storage with search, tagging, and status tracking. Beads (`bd` CLI) provides this as a SQLite-backed issue tracker, and we've validated it works without git — just `bd init` in a standalone directory.

Rather than each skill reimplementing beads initialization, invocation, and error handling, we extract the common infrastructure into a shared library: `guppi-beads`.

## What guppi-beads Is

A small pure-Python library (zero third-party dependencies) that wraps the `bd` CLI for use by guppi skills. It handles:

- Locating the skill's beads data directory (XDG convention)
- Checking whether `bd` is installed
- Auto-initializing beads on first use
- Running `bd` commands with correct working directory
- Common query patterns (find by title, list issues)

## What guppi-beads Is NOT

- Not a CLI tool — no `guppi-beads` command, no entry point
- Not a skill — no SKILL.md, not discoverable by agents
- Not a beads replacement — it wraps the `bd` CLI, doesn't reimplement it
- Not required — skills that don't need persistent storage don't use it

## Architecture

### Storage Location

Each skill gets its own beads instance at its XDG data directory:

```
~/.local/share/guppi/<skill_name>/
└── .beads/
    ├── beads.db       # SQLite database
    └── config.yaml    # Beads config
```

Following guppi conventions from CLAUDE.md: `~/.local/share/guppi/<name>/` for important, portable user data.

### No Git Required

Skills use beads as a local database only. No git hooks, no JSONL sync, no daemon. The `bd init` call uses `--skip-hooks --skip-merge-driver`. Skills that want git-backed sync can add it later independently.

### Graceful Degradation

If `bd` is not installed:
- `available()` returns `False`
- `ensure()` returns `False`
- `run()` returns a failed `CompletedProcess`
- Skills are responsible for deciding whether to error or silently skip

This means skills can treat beads as optional — core functionality works without it, metadata features are additive.

## API Surface

### BeadsStore

```python
from guppi_beads import BeadsStore

store = BeadsStore("spiker")                # skill name determines data dir
store = BeadsStore("spiker", prefix="spike") # custom issue prefix
```

#### Methods

**`available() -> bool`**
Check if the `bd` CLI is on PATH.

**`ensure() -> bool`**
Initialize beads if not already initialized. Returns True if beads is usable (bd installed + database exists or was created). Safe to call repeatedly — no-ops if already initialized.

**`run(args: list[str]) -> subprocess.CompletedProcess`**
Run a `bd` command with `cwd` set to the skill's data directory. Returns the CompletedProcess so callers can check returncode, stdout, stderr. Captures output by default.

**`find_by_title(title: str) -> dict | None`**
Find a single issue by exact title match. Returns the issue dict or None. Uses `bd list --json` with post-filter for exact match.

**`list_issues(status: str | None = None, all: bool = False) -> list[dict]`**
Fetch all issues as dicts. Optional status filter. `all=True` includes closed issues.

### Properties

**`data_dir -> Path`**
The skill's data directory (`~/.local/share/guppi/<skill_name>/`).

**`initialized -> bool`**
Whether the `.beads/beads.db` file exists.

## Usage by Skills

### Dependency Declaration

```toml
# spiker/pyproject.toml
[project]
dependencies = [
    "typer>=0.9.0",
    "guppi-beads>=0.1.0",
]

[tool.uv.sources]
guppi-beads = { path = "../lib/beads" }
```

### Example: Spiker

```python
from guppi_beads import BeadsStore

store = BeadsStore("spiker", prefix="spike")

# Auto-init on first use
if store.ensure():
    store.run(["create", "2026-03-02-redis-test", "--description", "Testing pub/sub"])

# Query
issues = store.list_issues()
issue = store.find_by_title("2026-03-02-redis-test")
```

### Example: Tracker

```python
from guppi_beads import BeadsStore

store = BeadsStore("tracker", prefix="trk")

if store.ensure():
    store.run(["create", "Read DDIA chapter 5", "--labels", "toread"])
```

## Project Structure

```
lib/beads/
├── pyproject.toml
├── docs/
│   └── design/
│       └── 2026-03-02-shared-beads-integration.md
├── src/
│   └── guppi_beads/
│       ├── __init__.py      # __version__, re-export BeadsStore
│       └── store.py         # BeadsStore class
└── tests/
    └── test_store.py
```

Lives in `lib/` (not top-level) to signal "library, not skill."

## Open Questions

- Should `BeadsStore` support a custom data directory override (e.g., for testing or non-XDG setups)?
- Should there be a `search(query)` convenience method, or leave that to `run(["search", ...])`?
