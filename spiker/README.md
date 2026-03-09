# Spiker

Manage experimental spike projects in a centralized, searchable location.

**Status:** Active | **Version:** 0.3.0 | **Created:** 2026-02-12 | **Updated:** 2026-03-09

## What it does

Spiker gives every experiment a home. Instead of scattering throwaway projects across your filesystem, spiker keeps them in one directory (`~/src/spikes/` by default), date-stamped and searchable. Each spike gets tracked with metadata — summaries, tags, and lifecycle status — so you can find that Redis caching experiment from three weeks ago without digging through folders.

## When to use it

- Starting a quick experiment or proof of concept
- Exploring a library, API, or technique you haven't used before
- Building something you're not sure will survive the week
- Trying to find that spike you made last month

## Quick start

```bash
# Create a new spike
guppi-spiker new redis-caching

# Create one with a random name (good for "just let me try something")
guppi-spiker new

# See what you've been working on
guppi-spiker list

# Jump into a spike
cd $(guppi-spiker path redis)
```

## What to expect

When you run `guppi-spiker new`, it:

1. Creates a dated directory (e.g., `2026-03-04-redis-caching/`)
2. Initializes a git repo inside it
3. Drops an `AGENTS.md` with session protocol for AI agents
4. Tracks the spike in beads for metadata and search
5. Prints the path so you can `cd` into it

If you give it a name that already exists, it returns the existing path — no duplicates.

## Lifecycle

Spikes move through a simple lifecycle:

```
open → in_progress → done
                  ↘ deferred (parked)
```

- **open** — just created, not started yet
- **in_progress** — actively working on it
- **deferred** — parked for later (`guppi-spiker park <query>`)
- **done** — finished, hidden from default list (`guppi-spiker done <query>`)

## Auto-summarize

Spiker can automatically summarize your spike sessions using a Claude Code SessionEnd hook. When you end a Claude Code session in a spike directory, it reads the session transcript, calls Claude Haiku for a one-line summary, and stores it in beads.

Run `guppi-spiker init` once per machine to set up the hook. No API key needed — it uses the `claude` CLI with your existing auth.

## Commands

### `guppi-spiker init`

One-time per-machine setup. Installs a Claude Code SessionEnd hook for auto-summarize and ensures the beads store is ready. Idempotent — safe to run multiple times.

### `guppi-spiker new [name]`

Create a new spike. If `name` is omitted, generates a random one (e.g., `fuzzy-teal-otter`).

- `--summary` / `-s` — one-line description
- `--no-git` — skip git init

### `guppi-spiker list`

List all spikes, most recent first.

- `--all` / `-a` — include done/closed spikes
- `--status` — filter by status (open, in_progress, deferred, closed)

### `guppi-spiker find <query>`

Search spikes by slug, summary, and tags.

### `guppi-spiker path <query>`

Print the path to the most recent matching spike. Designed for shell composition:

```bash
cd $(guppi-spiker path redis)
```

### `guppi-spiker describe <query> <summary>`

Set or update a spike's one-line summary.

### `guppi-spiker tag <query> <tags...>`

Add tags to a spike for better searchability.

### `guppi-spiker park <query>`

Park a spike — marks it as deferred. Still visible in `list`, signaling "paused, not abandoned."

### `guppi-spiker done <query>`

Mark a spike as done. Hidden from `list` unless you pass `--all`.

### `guppi-spiker purge`

Delete spikes that have no summary (empty/throwaway sessions). Skips today's spikes. Shows a confirmation table before deleting.

- `--force` / `-f` — skip confirmation

### `guppi-spiker summarize --from-hook`

Hook-only command called by the SessionEnd hook. Not intended for manual use — use `describe` for manual summaries.

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SPIKER_PATH` | `~/src/spikes` | Root directory for all spikes |

## Prerequisites

- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skill install`)
- [guppi-beads](../lib/beads/) (for metadata tracking)
