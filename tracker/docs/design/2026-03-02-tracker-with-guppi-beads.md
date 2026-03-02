# Tracker — Revised Design with guppi-beads

**Date:** 2026-03-02
**Status:** Design
**Supersedes:** 2026-02-27-cross-project-tracker.md

## What Changed

The original design had three open questions about how to use beads. Now that `guppi-beads` exists as a shared library, the answer is clear: `BeadsStore("tracker", prefix="trk")`. This resolves the "wrap beads CLI" vs "use as library" question — we wrap the CLI through guppi-beads, which handles init, cwd, and graceful degradation.

## Core Concept

A global catch-all for ideas, tasks, reading lists, and async work that doesn't belong to any specific project. Organization is via **tags**, not separate lists.

```bash
guppi-tracker add "Try building a Chrome extension with Plasmo" --tag idea
guppi-tracker add "Read DDIA chapter 5" --tag toread
guppi-tracker list --tag toread
guppi-tracker done trk-a3f
```

## Architecture

### Storage

`BeadsStore("tracker", prefix="trk")` — data lives at `~/.local/share/guppi/tracker/.beads/`. This is a standalone beads instance, no git repo needed (uses `--skip-hooks --skip-merge-driver`).

### No Git Sync (for now)

The original design envisioned a dedicated git remote for cross-machine sync. Deferring this — the immediate value is local capture and query. Sync can be layered on later without changing the API.

### Tags as First-Class

Every item gets zero or more tags via beads labels. Suggested conventions (not enforced):

| Tag | Purpose |
|-----|---------|
| `toread` | Articles, papers, docs |
| `towatch` | Videos, talks |
| `idea` | Things to try or explore |
| `task` | Actionable work items |
| `followup` | Check back on later |
| `buy` | Things to purchase |

Users can use any tags they want — these are just conventions.

## Commands

### `add <title> [--tag TAG...] [--note "..."]`

Create a new tracked item. Auto-inits beads on first use.

- Title becomes the beads issue title
- Tags become beads labels
- Note becomes the beads description
- Priority defaults to P2 (medium)

### `list [--tag TAG] [--all]`

Rich table of open items, most recent first. Columns: ID, title, tags.

- Default: open items only
- `--tag`: filter to items with this tag (can repeat for AND)
- `--all`: include closed items

### `done <id>`

Close an item by exact beads ID (e.g., `trk-a3f`).

### `tag <id> <tags...>`

Add tags to an existing item by exact beads ID.

### `show <id>`

Show full details of an item (delegates to `bd show`).

### `search <query>`

Full-text search across titles and descriptions (delegates to `bd search`).

## What's NOT in Scope

- **`sync` command** — deferred; no git remote for now
- **`priority` flag** — beads supports it, but keep the CLI simple; users can use `bd update` directly if they want priorities
- **`untag` command** — use `bd update --remove-label` directly
- **Linking to project issues** — interesting but complex; defer
- **Auto-tagging** — infer tags from title text (heuristics or LLM); for now items are untagged unless `--tag` is provided

## Implementation Notes

### Dependencies

```toml
dependencies = [
    "typer>=0.9.0",
    "rich>=14.0.0",
    "guppi-beads>=0.1.0",
]

[tool.uv.sources]
guppi-beads = { path = "../lib/beads" }
```

### Store Setup

```python
from guppi_beads import BeadsStore
_store = BeadsStore("tracker", prefix="trk")
```

### Graceful Degradation

If `bd` is not installed, all commands print a clear error and exit. Unlike spiker (where beads is optional), tracker's entire purpose is beads-backed storage — there's no fallback mode.

## Resolved Decisions

- **`list` shows tags column** — yes, include it
- **`add` without `--tag`** — creates an untagged item, no prompt (auto-tagging deferred)
