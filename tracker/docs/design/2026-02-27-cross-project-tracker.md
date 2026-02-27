# Cross-Project Tracker

**Date:** 2026-02-27
**Status:** Idea

## Motivation

Need a single place to capture and track ideas, tasks, reading lists, and async work that spans multiple projects. Currently using beads per-project, but there's no global tracker for cross-cutting items like "try X", "read Y", or "remember to follow up on Z".

## Core Design

### Built on Beads

Use beads as the underlying engine — JSONL data files, git as sync/persistence, SQL cache for queries. This gives us:
- Git-backed persistence and sync across machines
- Agent-friendly data format (JSONL)
- Fast querying via SQL cache
- Existing dependency tracking infrastructure

### Global Location

Unlike per-project beads, tracker lives in a global XDG location:
- Data: `~/.local/share/guppi/tracker/` (contains the git repo + .beads/)
- Cache: `~/.cache/guppi/tracker/` (SQL cache)

This is its own git repo, synced independently from any project.

### Tags Over Lists

Everything is an item. Organization is via tags, not separate lists:
- `toread` — articles, papers, docs to read
- `towatch` — videos, talks to watch
- `idea` — things to try or explore
- `task` — actionable work items
- `followup` — things to check back on

Tags are first-class, not an afterthought. Items can have multiple tags.

### Portability

Must work on machines without Homebrew (e.g., work laptop):
- Python 3.11+ only (no native dependencies)
- Git for sync (universally available)
- No OS-specific features

## Potential Commands

- `add <title> [--tag TAG...]` — capture a new item
- `list [--tag TAG] [--status STATUS]` — query items
- `show <id>` — detailed view
- `done <id>` — mark complete
- `tag <id> <tag>` — add a tag
- `search <query>` — full-text search
- `sync` — push/pull with remote

## Relationship to Beads

Options for using beads:
1. **Wrap beads CLI** — tracker calls `bd` with `--root ~/.local/share/guppi/tracker`
2. **Use beads as a library** — import beads Python modules directly
3. **Fork/adapt beads format** — use the same JSONL/git conventions but independent implementation

Option 1 is simplest. Need to check if beads supports `--root` or equivalent.

## Agent Integration

Agents should be able to:
- Add items conversationally ("Oh, I should remember X" → `tracker add`)
- Query relevant items ("What was I going to read about caching?" → `tracker search`)
- Track async work ("Here's what happened with the OpenClaw setup" → `tracker update`)
- Surface items proactively ("You have 3 unread items tagged 'toread'")

## Open Questions

- Does beads support a `--root` flag for pointing to an arbitrary directory?
- How to handle dependencies across tracker items and project beads issues?
- Should tracker items link to project-specific beads issues?
- What's the sync story — dedicated remote repo, or part of a dotfiles repo?
- Should there be a `priority` field, or is ordering by tags/dates sufficient?
