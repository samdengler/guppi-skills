# Spiker MVP

Inspired by [tobi/try](https://github.com/tobi/try) — a tool for managing experimental coding projects in a centralized, searchable location.

## Problem

Developers constantly create throwaway spike/experiment directories scattered across their filesystem. They get lost, can't be found later, and lack context about what was being explored.

## Concept

`guppi-spiker` organizes spike projects into a single directory with date-prefixed naming, search, and optional git init. It works as a CLI for humans and as an agent skill for AI assistants that need to scaffold experiments.

## Commands

### `guppi-spiker new [name]`

Create a new spike directory.

```bash
guppi-spiker new redis-caching
# Creates ~/src/spikes/2026-02-12-redis-caching/

guppi-spiker new
# Creates ~/src/spikes/2026-02-12-murky-green-giraffe/
```

- If `name` is provided, creates `YYYY-MM-DD-<name>/`
- If no `name`, generates a random `adjective-color-animal` slug
- Initializes a git repo by default (`--no-git` to skip)
- Prints the full path to stdout

**Random name generation:** Built-in word lists (no third-party deps). Format: `<adjective>-<color>-<animal>` (e.g., `fuzzy-teal-otter`, `swift-amber-falcon`).

### `guppi-spiker list`

List all spikes, most recent first.

```bash
guppi-spiker list
# 2026-02-12  redis-caching
# 2026-02-12  murky-green-giraffe
# 2026-02-10  graphql-subscriptions
```

### `guppi-spiker find <query>`

Search spikes by substring match.

```bash
guppi-spiker find redis
# ~/src/spikes/2026-02-12-redis-caching
```

Matches against the slug portion of the directory name. Prints full paths.

### `guppi-spiker path <query>`

Print the path to the first matching spike (for shell integration).

```bash
cd $(guppi-spiker path redis)
```

Like `find` but returns only the first (most recent) match.

### `guppi-spiker skill install` / `guppi-spiker skill show`

Standard guppi skill management commands (per CLAUDE.md).

## Configuration

- **Spike root directory:** `SPIKER_PATH` env var, default `~/src/spikes`

## Non-Goals (MVP)

- No clone/template support
- No TUI/interactive browser
- No fuzzy matching (substring only)
- No cleanup/archive commands
- No metadata files per spike
- No shell function wrapper (use `cd $(...)` pattern)
