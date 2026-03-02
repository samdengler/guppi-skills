# Alfred Quick Capture for Tracker

**Date:** 2026-03-02
**Status:** Idea

## Motivation

The best capture tool is the one with the least friction. Right now, adding an idea to tracker requires opening a terminal and typing `guppi-tracker add "..." --tag idea`. That's too many steps when inspiration strikes mid-flow.

Alfred is already the fastest way to invoke anything on macOS. A keyword + text is all it should take:

```
⌘Space → .i build a chrome extension with plasmo → Enter
```

Done. Idea tracked. Back to what you were doing in under 2 seconds.

## Design

### Keywords → Tags

Each keyword maps to a `guppi-tracker add` call with pre-defined tags:

| Keyword | Tag | Example |
|---------|-----|---------|
| `.i` | `idea` | `.i build a chrome extension with plasmo` |
| `.t` | `task` | `.t update snapper CDP version` |
| `.r` | `toread` | `.r https://architecture-notes.com/cell-arch` |
| `.b` | `buy` | `.b replacement AirPods tips` |
| `.f` | `followup` | `.f check if PR was merged` |

The dot prefix keeps them short and avoids colliding with other Alfred keywords. Single character after the dot for muscle memory.

### Implementation

An Alfred workflow with one Script Filter per keyword. Each runs:

```bash
/Users/samdengler/.local/bin/guppi-tracker add "{query}" --tag idea
```

The workflow is just a thin launcher — all logic stays in tracker. No Alfred-specific state or configuration.

### Notification

Alfred can show a brief notification on success ("Tracked: build a chrome extension with plasmo"). On failure (bd not installed, etc.), show the error. This is built into Alfred's Post Notification output.

### Workflow Structure

```
tracker-capture.alfredworkflow
├── Keyword: .i → Run Script → Post Notification
├── Keyword: .t → Run Script → Post Notification
├── Keyword: .r → Run Script → Post Notification
├── Keyword: .b → Run Script → Post Notification
└── Keyword: .f → Run Script → Post Notification
```

Each is identical except for the keyword and `--tag` value. Could also be a single Universal Action with a tag picker, but separate keywords are faster — no second step.

## What I Like

- **Zero friction** — Alfred is already muscle memory, adding a keyword is trivial
- **No new infrastructure** — tracker does all the work, Alfred is just a launcher
- **Extensible** — new keywords are a 30-second copy-paste in Alfred
- **Works offline** — no network, no API, just a local CLI call

## Open Questions

- **Where does the workflow live?** Options:
  - In `tracker/alfred/` and manually import into Alfred
  - Managed by a future "futzer" workflow (generate Alfred workflows from config)
  - Just build it by hand in Alfred and don't version-control it
- **Should `.r` extract a title from the URL?** Could add a `--url` flag to tracker that fetches the page title automatically. Nice but adds complexity and network dependency.
- **Multiple tags on capture?** Probably not worth it — keep capture fast, tag later with `guppi-tracker tag`.
- **Should there be a `.q` (quick, no tag)?** For things that don't fit a category. Could just be `.t` with a generic `inbox` tag.
