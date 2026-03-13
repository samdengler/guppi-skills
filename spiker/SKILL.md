---
name: spiker
description: >
  Manage experimental spike projects in a centralized, searchable location.
  Use when you need to create, find, or navigate to spike/experiment directories.
allowed-tools: "Bash(guppi-spiker:*)"
version: "0.4.1"
author: "Sam Dengler"
license: "MIT"
---

# Spiker — Spike project manager

Organizes experimental coding projects into a single directory with date-prefixed naming, search, metadata tracking, and optional git init. Creates directories like `2026-02-12-redis-caching` under a configurable root. Optionally tracks summaries, tags, and lifecycle status via beads.

## Commands

### `guppi-spiker new [name]`

Create a new spike directory.

**Arguments:**
- `name` (optional) — slug for the directory. If omitted, generates a random name (e.g., `fuzzy-teal-otter`)

**Options:**
- `--no-git` — skip git init
- `--summary` / `-s` — one-line summary (stored in beads)

**Examples:**
```bash
guppi-spiker new redis-caching    # ~/src/spikes/2026-02-12-redis-caching/
guppi-spiker new                  # ~/src/spikes/2026-02-12-fuzzy-teal-otter/
guppi-spiker new redis-test --summary "Testing pub/sub for notifications"
```

### `guppi-spiker list [query]`

List all spikes with summaries, most recent first. Optional query filters by slug substring.

**Options:**
- `--all` / `-a` — include done (closed) spikes
- `--status` — filter by status (open, in_progress, deferred, closed)

```bash
guppi-spiker list
guppi-spiker list redis
guppi-spiker list --all
guppi-spiker list --status deferred
```

### `guppi-spiker go <query>`

Print the path to the most recent matching spike. Use with `cd $(...)`.

```bash
cd $(guppi-spiker go redis)
```

### `guppi-spiker describe <query> <summary>`

Set or update a spike's summary.

```bash
guppi-spiker describe redis "Testing pub/sub for notifications"
```

### `guppi-spiker tag <query> <tags...>`

Add tags to a spike.

```bash
guppi-spiker tag redis backend caching
```

### `guppi-spiker park <query>`

Park a spike (mark as deferred — paused but still visible in list).

```bash
guppi-spiker park redis
```

### `guppi-spiker done <query>`

Mark a spike as done (closes the beads issue, hidden from default list).

```bash
guppi-spiker done redis
```

## Configuration

Set `SPIKER_PATH` env var to change the spike root directory (default: `~/src/spikes`).

## Skill Management

```bash
guppi-spiker skill install   # Register with guppi-cli
guppi-spiker skill show      # Display SKILL.md contents
```
