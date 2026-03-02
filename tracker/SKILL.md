---
name: tracker
description: >
  Cross-project task and idea tracker built on beads. Use when you need to
  capture ideas, tasks, reading lists, or track async work across projects.
allowed-tools: "Bash(guppi-tracker:*)"
version: "0.2.0"
author: "Sam Dengler"
license: "MIT"
---

# Tracker — cross-project task and idea tracker

Track ideas, tasks, reading lists, and async work items in a single place that works across projects. Built on beads for persistent storage and agent-friendly querying.

## Commands

### `guppi-tracker add <title> [--tag TAG...] [--note "..."]`

Add a new tracked item. Auto-initializes beads on first use.

**Options:**
- `--tag` / `-t` — tag the item (repeatable)
- `--note` / `-n` — description or note

**Examples:**
```bash
guppi-tracker add "Read DDIA chapter 5" --tag toread
guppi-tracker add "Try Plasmo for Chrome extensions" --tag idea --note "Framework for building Chrome extensions"
```

### `guppi-tracker list [--tag TAG] [--all]`

List tracked items in a table with ID, title, and tags.

**Options:**
- `--tag` / `-t` — filter by tag
- `--all` / `-a` — include closed items

```bash
guppi-tracker list
guppi-tracker list --tag toread
guppi-tracker list --all
```

### `guppi-tracker done <id>`

Mark an item as done by exact beads ID.

```bash
guppi-tracker done trk-a3f
```

### `guppi-tracker tag <id> <tags...>`

Add tags to an item.

```bash
guppi-tracker tag trk-a3f backend caching
```

### `guppi-tracker show <id>`

Show full details of an item.

```bash
guppi-tracker show trk-a3f
```

### `guppi-tracker search <query>`

Full-text search across titles and descriptions.

```bash
guppi-tracker search "Chrome extension"
```

### `guppi-tracker review`

Process inbox — walk through untagged items and tag, done, or skip them.

For each untagged item, you'll be prompted to:
- **(t)ag** — assign tags (space-separated)
- **(d)one** — mark complete
- **(s)kip** — leave for later (default)
- **(q)uit** — stop reviewing

```bash
guppi-tracker review
```

## Tag Conventions

| Tag | Purpose |
|-----|---------|
| `toread` | Articles, papers, docs |
| `towatch` | Videos, talks |
| `idea` | Things to try or explore |
| `task` | Actionable work items |
| `followup` | Check back on later |
| `buy` | Things to purchase |

## Skill Management

```bash
guppi-tracker skill install   # Register with guppi-cli
guppi-tracker skill show      # Display SKILL.md contents
```
