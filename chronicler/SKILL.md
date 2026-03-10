---
name: chronicler
description: >
  Research historical events from local history sources (Chrome, terminal).
  Use when you need to find what happened, when it happened, or retrace activity.
allowed-tools: "Bash(guppi-chronicler:*)"
version: "0.1.1"
author: "Sam Dengler"
license: "MIT"
---

# Chronicler — Research historical events from local sources

Chronicler searches local history sources (Chrome browser history, terminal/shell history) to answer questions about past activity. Sources are pluggable — register only the ones available on each machine.

## Commands

### `guppi-chronicler search [QUERY] [--source NAME] [--since DATE] [--until DATE] [--limit N] [--timeout SECS]`

Search across all enabled sources (or a specific one). Returns results sorted by time, most recent first.

**Arguments:**
- `query` — text to search for (optional; omit for all recent history)

**Options:**
- `--source` / `-s` — limit to a specific registered source
- `--since` — results after this date/time (ISO 8601 or natural: "yesterday", "3 days ago")
- `--until` — results before this date/time
- `--limit` / `-n` — max results (default: 50)
- `--timeout` / `-t` — max seconds to wait (default: 10). Returns partial results on timeout.

### `guppi-chronicler source list`

List registered sources and their status.

### `guppi-chronicler source add <name> --type <type> [--path <path>]`

Register a new history source. Runs prerequisite check after registering.

### `guppi-chronicler source remove <name>`

Unregister a source.

### `guppi-chronicler source enable <name>` / `source disable <name>`

Toggle a source on/off.

### `guppi-chronicler source detect [--apply]`

Scan for available history sources. With `--apply`, auto-register detected sources.

### `guppi-chronicler source init <name> [--apply]`

Check prerequisites for a source. With `--apply`, fix them automatically.

## Examples

```bash
# Search all sources for "github"
guppi-chronicler search github

# Recent terminal history from today
guppi-chronicler search --source terminal --since today

# Everything from the last hour
guppi-chronicler search --since "1 hours ago" --limit 100

# Set up on a new machine
guppi-chronicler source detect --apply
guppi-chronicler source init terminal --apply
```

## Skill Management

```bash
guppi-chronicler skill install   # Register with guppi-cli
guppi-chronicler skill show      # Display SKILL.md contents
```
