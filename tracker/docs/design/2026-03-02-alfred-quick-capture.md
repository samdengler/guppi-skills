# Alfred Quick Capture for Tracker

**Date:** 2026-03-02
**Status:** Implemented (v1 — `.q` inbox only)

## Motivation

The best capture tool is the one with the least friction. Right now, adding an idea to tracker requires opening a terminal and typing `guppi-tracker add "..." --tag idea`. That's too many steps when inspiration strikes mid-flow.

Alfred is already the fastest way to invoke anything on macOS. A keyword + text is all it should take:

```
⌘Space → .q build a chrome extension with plasmo → Enter
```

Done. Captured to inbox. Back to what you were doing in under 2 seconds. Process later with `guppi-tracker review`.

## Design (v1 — GTD Inbox)

### Single keyword: `.q`

Start with one keyword that captures everything untagged to the inbox:

```
.q build a chrome extension with plasmo
```

This follows GTD: capture fast, categorize later. The `review` command walks through untagged items and lets you tag, done, or skip each one.

### Implementation

An Alfred workflow with one Keyword → Run Script → Post Notification:

```bash
/Users/samdengler/.local/bin/guppi-tracker add "{query}"
```

No `--tag` flag. Items land in the inbox untagged. Alfred shows a "Tracked" notification on success.

### Workflow Structure

```
tracker/alfred/
├── info.plist              # Alfred workflow definition
└── install.sh              # Build .alfredworkflow and import
```

Run `./install.sh` to build and open the workflow in Alfred.

### Review Flow

```bash
guppi-tracker review        # Walk through untagged items
```

For each item: **(t)ag**, **(d)one**, **(s)kip**, or **(q)uit**.

## What I Like

- **Zero friction** — one keyword, no categorization needed at capture time
- **GTD inbox** — capture everything, process later in batch
- **No new infrastructure** — tracker does all the work, Alfred is just a launcher
- **Works offline** — no network, no API, just a local CLI call

## Future: Multiple Keywords

If the single `.q` keyword feels limiting, add per-tag shortcuts later:

| Keyword | Tag | Example |
|---------|-----|---------|
| `.q` | *(none)* | `.q build a chrome extension with plasmo` |
| `.i` | `idea` | `.i build a chrome extension with plasmo` |
| `.t` | `task` | `.t update snapper CDP version` |
| `.r` | `toread` | `.r https://architecture-notes.com/cell-arch` |
| `.b` | `buy` | `.b replacement AirPods tips` |
| `.f` | `followup` | `.f check if PR was merged` |

Each is a copy of the `.q` workflow with `--tag <name>` appended to the script.

## Open Questions (Deferred)

- **Should `.r` extract a title from the URL?** Could add a `--url` flag to tracker that fetches the page title. Nice but adds complexity.
- **Where does the workflow live long-term?** Currently in `tracker/alfred/`, imported manually. Could be managed by futzer in the future.
