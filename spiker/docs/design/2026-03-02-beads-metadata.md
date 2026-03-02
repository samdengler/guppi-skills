# Beads Metadata Tracking for Spiker

**Date:** 2026-03-02
**Status:** Approved

## Problem

Spiker is purely filesystem-based — no metadata, no summaries, no tags. Users lose track of what spikes are about across sessions. Random-name spikes (e.g., `fuzzy-teal-otter`) are especially opaque days later.

## Solution

Use beads (`bd` CLI) as a lightweight SQLite database to track spike metadata. Each spike gets a beads issue with a summary, tags, and lifecycle status.

## Architecture

- **Beads database** lives at `~/.local/share/guppi/spiker/.beads/` (XDG data dir)
- **No git required** — `bd init --skip-hooks --skip-merge-driver`; git sync can be added later
- **Filesystem remains primary** — beads is supplementary; spikes without issues still appear
- **Graceful degradation** — if `bd` isn't installed, spiker works exactly as before
- **AGENTS.md template** — new spikes include instructions for agents to update metadata
- **Shared library** — uses `guppi-beads` (`lib/beads/`) for init/run/query plumbing

## Data Model

Each spike maps to a beads issue:

| Beads field | Spike concept | Example |
|-------------|---------------|---------|
| title | dirname | `2026-03-02-redis-test` |
| description | summary | "Testing Redis pub/sub for notifications" |
| labels | tags | `redis`, `backend` |
| status | lifecycle | open (active), deferred (parked), closed (done) |

The dirname-as-title provides an unambiguous key for matching filesystem spikes to beads issues.

### Status Mapping

All statuses are native to `bd`:

| Spiker concept | bd status |
|----------------|-----------|
| active | `open` |
| working | `in_progress` |
| parked | `deferred` |
| done | `closed` |

## Commands

### Modified

- `new [name] [--summary "..."]` — creates beads issue alongside directory; auto-inits beads on first run
- `list [--all] [--status STATUS]` — Rich table with summary column; defaults to active+parked; `--all` includes done
- `find <query>` — searches slugs + summaries + tags via `bd search`

### New

- `describe <query> "summary"` — set/update spike summary
- `tag <query> tag1 [tag2...]` — add tags
- `park <query>` — mark as deferred (paused but visible)
- `done <query>` — close the beads issue

### Unchanged

- `path <query>` — returns path for shell integration
- `skill install` / `skill show`

## AGENTS.md Template

Every new spike gets an AGENTS.md:

```markdown
# Spike: {slug}

## Session Protocol

Before ending a session, update this spike's metadata:

```bash
guppi-spiker describe {slug} "one-line summary of what you explored"
guppi-spiker tag {slug} topic1 topic2
guppi-spiker done {slug}  # if the spike is complete
```
```

## Edge Cases

- **`bd` not installed** — beads operations silently skip; core spiker functionality unchanged
- **Old spikes without issues** — show in list with empty metadata; `describe`/`tag`/`park`/`done` auto-create an issue
- **Deleted spike with orphaned issue** — filtered out (filesystem is primary)
- **Multiple matches** — most recent wins (consistent with `path` command)

## Resolved Decisions

- **No `init` command** — `ensure()` auto-runs on first `new`; no need for a standalone command
- **`list` shows summary only** — no labels column; keeps output clean
- **`describe .` deferred** — not implementing dot-as-cwd shorthand in this iteration
- **`park` maps to `deferred`** — native bd status, no workaround needed
- **`--summary`/`-s` on `new`** — flag name confirmed
- **`find` uses `bd search`** — will work through any sync issues as they arise
