---
name: spiker
description: >
  Manage experimental spike projects in a centralized, searchable location.
  Use when you need to create, find, or navigate to spike/experiment directories.
allowed-tools: "Bash(guppi-spiker:*)"
version: "0.1.0"
author: "Sam Dengler"
license: "MIT"
---

# Spiker — Spike project manager

Organizes experimental coding projects into a single directory with date-prefixed naming, search, and optional git init. Creates directories like `2026-02-12-redis-caching` under a configurable root.

## Commands

### `guppi-spiker new [name]`

Create a new spike directory.

**Arguments:**
- `name` (optional) — slug for the directory. If omitted, generates a random name (e.g., `fuzzy-teal-otter`)

**Options:**
- `--no-git` — skip git init

**Examples:**
```bash
guppi-spiker new redis-caching    # ~/src/spikes/2026-02-12-redis-caching/
guppi-spiker new                  # ~/src/spikes/2026-02-12-fuzzy-teal-otter/
guppi-spiker new foo --no-git     # No git init
```

### `guppi-spiker list`

List all spikes, most recent first.

```bash
guppi-spiker list
```

### `guppi-spiker find <query>`

Search spikes by substring match. Prints full paths.

```bash
guppi-spiker find redis
```

### `guppi-spiker path <query>`

Print the path to the most recent matching spike. Use with `cd $(...)`.

```bash
cd $(guppi-spiker path redis)
```

## Configuration

Set `SPIKER_PATH` env var to change the spike root directory (default: `~/src/spikes`).

## Skill Management

```bash
guppi-spiker skill install   # Register with guppi-cli
guppi-spiker skill show      # Display SKILL.md contents
```
