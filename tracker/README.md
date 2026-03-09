# Tracker

Cross-project task and idea tracker built on beads.

**Status:** Active | **Version:** 0.2.0 | **Created:** 2026-03-08 | **Updated:** 2026-03-09

## What it does

Tracker gives you a single place to capture ideas, tasks, reading lists, and async work items that span projects. Instead of scattering TODOs across sticky notes, text files, and Slack threads, tracker stores everything in beads with tags and full-text search. Items are lightweight -- a title and optional note -- so there's zero friction to capture something before it slips away.

## When to use it

- Jotting down an idea before you forget it
- Queuing up articles, papers, or talks to read/watch later
- Tracking a task that doesn't belong to any single project
- Reviewing your inbox of untagged items to stay organized
- Searching for that thing you captured last week

## Quick start

```bash
# Capture something quickly
guppi-tracker add "Read DDIA chapter 5" --tag toread

# Capture an idea with a note
guppi-tracker add "Try Plasmo for Chrome extensions" --tag idea --note "Framework for building Chrome extensions"

# See what you're tracking
guppi-tracker list

# Filter by tag
guppi-tracker list --tag toread

# Find something specific
guppi-tracker search "Chrome"

# Mark it done
guppi-tracker done trk-a3f
```

## What to expect

When you run `guppi-tracker add`, it:

1. Auto-initializes the beads store on first use (no setup needed)
2. Creates a tracked item with a unique ID (e.g., `trk-a3f`)
3. Applies any tags you specified
4. Confirms the item was created

Items are stored persistently via beads and survive across sessions, projects, and machines (if you sync your beads store).

## Tag conventions

Use tags to categorize items. These are suggestions, not rules -- use whatever makes sense to you.

| Tag | Purpose |
|-----|---------|
| `toread` | Articles, papers, docs |
| `towatch` | Videos, talks |
| `idea` | Things to try or explore |
| `task` | Actionable work items |
| `followup` | Check back on later |
| `buy` | Things to purchase |

## Commands

### `guppi-tracker add <title>`

Add a new tracked item.

- `--tag` / `-t` -- tag the item (repeatable, e.g., `--tag idea --tag backend`)
- `--note` / `-n` -- description or note

### `guppi-tracker list`

List tracked items in a table with ID, title, and tags.

- `--tag` / `-t` -- filter by tag
- `--all` / `-a` -- include closed/done items

### `guppi-tracker done <id>`

Mark an item as done by its beads ID (e.g., `trk-a3f`). Done items are hidden from `list` unless you pass `--all`.

### `guppi-tracker tag <id> <tags...>`

Add one or more tags to an existing item.

```bash
guppi-tracker tag trk-a3f backend caching
```

### `guppi-tracker show <id>`

Show full details of an item, including title, description, tags, and status.

### `guppi-tracker search <query>`

Full-text search across titles and descriptions.

```bash
guppi-tracker search "Chrome extension"
```

### `guppi-tracker review`

Process your inbox -- walk through all untagged items one by one. For each item, you choose:

- **(t)ag** -- assign tags (space-separated)
- **(d)one** -- mark complete
- **(s)kip** -- leave for later (default)
- **(q)uit** -- stop reviewing

This is useful for batch-processing items you captured quickly without tags.

## Configuration

Tracker has no configuration files. It stores all data in the beads store, which is managed by `guppi-beads`. Items use the `trk` prefix for their IDs.

## Prerequisites

- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skill install`)
- [guppi-beads](../lib/beads/) (for persistent storage)
