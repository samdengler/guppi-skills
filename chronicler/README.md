# Chronicler

Research historical events from local history sources (Chrome, terminal).

**Status:** Active | **Version:** 0.1.0 | **Created:** 2026-03-09

## What it does

Chronicler searches your local history sources to answer questions about past activity. Instead of manually opening Chrome history or scrolling through terminal logs, chronicler gives you a single search interface across all of them. Results come back in a unified table, sorted by time, with source and kind labels so you know where each entry came from.

Sources are pluggable — register only the ones available on each machine. Currently supported source types: **chrome** (browser history) and **terminal** (shell history).

## When to use it

- Retracing what you were doing at a specific time
- Finding a URL you visited last week but didn't bookmark
- Searching terminal history for a command you ran days ago
- Getting a timeline of activity across browser and terminal

## Quick start

```bash
# Detect and register available sources
guppi-chronicler source detect --apply

# Fix any prerequisites (e.g., Chrome full-disk access)
guppi-chronicler source init chrome --apply

# Search across everything
guppi-chronicler search github

# Recent terminal commands from today
guppi-chronicler search --source terminal --since today
```

## What to expect

When you run `guppi-chronicler search`, it:

1. Searches all enabled sources concurrently
2. Merges results into a single list, sorted newest first
3. Renders a table with columns: Time, Source, Kind, Summary
4. Prints a source status footer showing which sources responded

If a source times out (default: 10 seconds), chronicler returns partial results from the sources that did respond and flags the slow one in the footer.

## Commands

### `guppi-chronicler search [QUERY]`

Search across all enabled sources (or a specific one). Returns results sorted by time, most recent first.

- `QUERY` — text to search for (optional; omit for all recent history)
- `--source` / `-s` — limit to a specific registered source
- `--since` — results after this date/time (ISO 8601 or natural: "yesterday", "3 days ago")
- `--until` — results before this date/time
- `--limit` / `-n` — max results (default: 50)
- `--timeout` / `-t` — max seconds to wait (default: 10)

```bash
# Search all sources for "github"
guppi-chronicler search github

# Everything from the last hour
guppi-chronicler search --since "1 hours ago" --limit 100

# Chrome history only, from the past week
guppi-chronicler search --source chrome --since "7 days ago"
```

### `guppi-chronicler source list`

List registered sources and their status (type, enabled, available).

### `guppi-chronicler source add <name> --type <type>`

Register a new history source. Runs a prerequisite check after registering.

- `--type` / `-t` — source type: `chrome` or `terminal`
- `--path` / `-p` — override the default data path

### `guppi-chronicler source remove <name>`

Unregister a source.

### `guppi-chronicler source enable <name>` / `source disable <name>`

Toggle a source on or off without removing it.

### `guppi-chronicler source detect [--apply]`

Scan the machine for available history sources. Without `--apply`, just reports what it finds. With `--apply`, auto-registers detected sources.

### `guppi-chronicler source init <name> [--apply]`

Check prerequisites for a source (e.g., Chrome needs full-disk access on macOS). Without `--apply`, lists issues. With `--apply`, attempts to fix them automatically.

## Configuration

Config lives at `~/.config/guppi/chronicler/config.json`. You rarely need to edit this directly — the `source` subcommands manage it.

The config tracks registered sources, each with:

| Field | Description |
|-------|-------------|
| `type` | Source adapter type (`chrome`, `terminal`) |
| `enabled` | Whether the source is searched by default |
| `path` | Custom data path override (null for default location) |

## Prerequisites

- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skill install`)
- **Chrome source:** Full Disk Access permission on macOS (chronicler reads the Chrome History SQLite database)
- **Terminal source:** Standard shell history file (e.g., `~/.zsh_history`, `~/.bash_history`)
