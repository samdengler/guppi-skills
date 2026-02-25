# Pluggable History Sources

**Date:** 2026-02-25
**Status:** Draft

## Problem

Agents (and humans) need to answer questions like "what did I do yesterday?" or "when did I last visit that site?" by querying local history sources. Different machines have different sources available — a work laptop may only have terminal history, while a personal machine also has Chrome.

## Design

### Dependencies Per Source

Source adapters may need third-party libraries (e.g., a future Safari adapter might need a plist parser). Rather than making every dependency required, source-specific dependencies are **optional extras** in pyproject.toml:

```toml
[project.optional-dependencies]
chrome = []          # stdlib sqlite3 is enough
terminal = []        # pure file parsing
# future examples:
# safari = ["biplist>=1.0"]
```

The core package (`guppi-chronicler`) has no source-specific dependencies — just typer. Each source adapter checks at import/runtime whether its dependencies are available and reports clearly if they're missing. This keeps the skill portable: install the base package anywhere, then only enable sources whose dependencies are satisfied.

For the initial two sources (chrome, terminal), both use only the stdlib — no extras needed.

### Source Registry

Sources are registered in `~/.config/guppi/chronicler/config.json`:

```json
{
  "sources": {
    "chrome": {
      "type": "chrome",
      "enabled": true,
      "path": null
    },
    "terminal": {
      "type": "terminal",
      "enabled": true,
      "path": null
    }
  }
}
```

Each source has a `type` (selects the adapter), `enabled` flag, and optional `path` override. When `path` is null, the adapter uses its default location. Sources can be added/removed per machine without affecting the skill itself.

### Built-in Source Types

#### `chrome` — Chrome Browser History

Reads from Chrome's SQLite `History` database.

- **Default path:** `~/Library/Application Support/Google/Chrome/Default/History` (macOS)
- Chrome locks the DB while running, so we **copy it to a temp file** before querying
- Queries the `urls` and `visits` tables
- Returns: URL, title, visit time, visit duration

#### `terminal` — Shell History

Reads shell history files.

- **zsh:** `~/.zsh_history` (extended format with timestamps)
- **bash:** `~/.bash_history` (no timestamps unless `HISTTIMEFORMAT` set)
- Auto-detects shell from `$SHELL` env var
- Parses zsh extended history format (`: timestamp:0;command`)

### CLI Commands

#### `search`

```
guppi-chronicler search <query> [--source NAME] [--since DATE] [--until DATE] [--limit N] [--timeout SECS]
```

Search across all enabled sources (or a specific one). Returns results sorted by time, most recent first.

- `query` — text to search for (substring match across URLs, titles, commands). Optional — omitting returns all recent history.
- `--source` / `-s` — limit to a specific registered source
- `--since` — only results after this date/time (ISO 8601 or natural: "yesterday", "last week", "3 days ago")
- `--until` — only results before this date/time
- `--limit` / `-n` — max results (default: 50)
- `--timeout` / `-t` — max seconds to wait for results (default: 10). Returns whatever results have been collected when the timeout fires. Partial results are marked in output.

When `query` is omitted, acts as a "recent history" command — returns the most recent entries across sources, still respecting `--since`/`--until`/`--limit`.

#### `source list`

```
guppi-chronicler source list
```

List registered sources and their status (enabled/disabled, type, whether the backing data is accessible).

#### `source add`

```
guppi-chronicler source add <name> --type <type> [--path <path>]
```

Register a new source. `--path` overrides the default location for the source type. After registering, automatically runs `source init` in check-only mode to show the source's readiness.

#### `source remove`

```
guppi-chronicler source remove <name>
```

Unregister a source.

#### `source enable` / `source disable`

```
guppi-chronicler source enable <name>
guppi-chronicler source disable <name>
```

Toggle a source on/off without removing its config.

#### `source detect`

```
guppi-chronicler source detect [--apply]
```

Scan the local machine for known source types (Chrome History DB, zsh/bash history files). Reports what's found. With `--apply`, registers all detected sources automatically.

Useful for onboarding — agents can call this to discover what's available without knowing the machine's setup.

#### `source init`

```
guppi-chronicler source init <name> [--apply]
```

Check prerequisites for a registered source and report what's needed. Without `--apply`, diagnostic only — shows what to fix. With `--apply`, makes the changes automatically.

**Per source type:**

- **terminal** — checks if `EXTENDED_HISTORY` is set in zsh config. If not, shows the lines to add to `~/.zshrc`. With `--apply`, appends them.
- **chrome** — checks if the History DB exists at the expected path. Checks macOS Full Disk Access permissions if the file isn't readable.
- **future sources** — checks for required Python dependencies, shows install command.

`.zshrc` is the correct place for history config (history is only relevant for interactive shells, not `.zshenv`).

Example output:

```
$ guppi-chronicler source init terminal

Checking terminal source requirements...

zsh detected. EXTENDED_HISTORY is not set.

Add the following to ~/.zshrc:

    setopt EXTENDED_HISTORY
    HISTTIMEFORMAT="%F %T "

Or run with --apply to add automatically:

    guppi-chronicler source init terminal --apply
```

### Timeout & Partial Results

Searching multiple sources can be slow (large Chrome DBs, huge shell histories). The `--timeout` flag sets a wall-clock deadline for the entire search.

**How it works:**

1. Sources are queried concurrently using `concurrent.futures.ThreadPoolExecutor`
2. Each source gets `timeout` seconds total (shared deadline, not per-source)
3. `as_completed()` collects results as they arrive
4. When the deadline passes, we stop waiting and return what we have
5. Output includes a footer noting which sources completed vs timed out

```
 Time                 Source    Kind     Summary
 2026-02-25 14:30:00  chrome    url      GitHub - guppi-skills repo
 2026-02-25 14:28:00  terminal  command  git push origin main

 Sources: chrome (ok), terminal (ok)
```

If a source times out:

```
 Time                 Source    Kind     Summary
 2026-02-25 14:28:00  terminal  command  git push origin main

 Sources: terminal (ok), chrome (timed out)
```

If a source errors (corrupt DB, permission denied), search still returns results from other sources:

```
 Time                 Source    Kind     Summary
 2026-02-25 14:28:00  terminal  command  git push origin main

 Sources: terminal (ok), chrome (error: permission denied)
```

This uses `concurrent.futures` from stdlib — no async framework needed.

### Date Parsing

Support both ISO 8601 and common natural language shortcuts. Implemented as simple keyword mappings in a `dates.py` module — no third-party dependency.

**Supported natural language:**
- `today`, `yesterday`
- `N days ago`, `N weeks ago`, `N hours ago`
- `last week`, `last month`
- `this week`, `this month`

**Fallback:** ISO 8601 (`2026-02-25`, `2026-02-25T14:30:00`)

Anything that doesn't match a known pattern gets passed to `datetime.fromisoformat()`. If that fails, error with examples.

### Source Adapter Interface

Each source type is a Python module in `guppi_chronicler/sources/`:

```
sources/
├── __init__.py
├── base.py       # Abstract base
├── chrome.py
└── terminal.py
```

```python
# base.py
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

@dataclass
class HistoryEntry:
    """A single history event from any source."""
    timestamp: datetime | None  # None for entries without timestamps
    source: str                 # registered source name
    kind: str                   # "url", "command", etc.
    summary: str                # display text (title, command)
    detail: str | None          # extra info (URL, working dir)

class SourceAdapter(ABC):
    @abstractmethod
    def search(
        self,
        query: str | None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
    ) -> list[HistoryEntry]:
        """Search this source for matching history entries."""
        ...

    @abstractmethod
    def available(self) -> bool:
        """Check if this source's backing data is accessible."""
        ...

    @abstractmethod
    def check_prereqs(self) -> list[str]:
        """Check prerequisites. Returns list of issues (empty = ready)."""
        ...

    @abstractmethod
    def apply_prereqs(self) -> list[str]:
        """Fix prerequisites automatically. Returns list of actions taken."""
        ...

    @abstractmethod
    def detect(self) -> bool:
        """Return True if this source type's data exists on this machine."""
        ...
```

### Result Merging

Results from multiple sources are merged by timestamp, most recent first. Entries without timestamps (e.g., bash history without `HISTTIMEFORMAT`) are grouped at the bottom under an "Undated" section.

### Output Format

Rich table for humans, one entry per row:

```
 Time                 Source    Kind     Summary
 2026-02-25 14:30:00  chrome    url      GitHub - guppi-skills repo
 2026-02-25 14:28:00  terminal  command  git push origin main
 2026-02-25 14:25:00  chrome    url      Stack Overflow - Python dataclasses

 Undated
 —                    terminal  command  export FOO=bar

 Sources: chrome (ok), terminal (ok)
```

For agent consumption, the table is sufficient — agents parse structured text well.

## Decisions

1. **Natural language dates** — yes, via simple keyword mappings (no dependency). ISO 8601 as fallback.
2. **Chrome profiles** — single default profile for now. Multiple profiles via `--path` override on `source add` if needed later.
3. **Per-source dependencies** — optional extras in pyproject.toml. Core has no source-specific deps. Initial sources (chrome, terminal) are stdlib-only.
4. **Empty query** — allowed. Returns all recent history, respecting time/limit filters.
5. **Undated entries** — grouped at the bottom of results, not interleaved with dated entries.
6. **Source errors** — non-fatal. Other sources still return results. Error reported in footer.
7. **`source add` runs `init` check** — after registering, automatically shows readiness status.
8. **Dotfile modifications** — diagnostic by default, `--apply` flag to make changes. Never modify dotfiles silently.
9. **History config location** — `.zshrc` (interactive shell only, not `.zshenv`).

## Open Questions

1. **Additional source types** — git log, VS Code recent files, Finder recents. Worth designing for but not building yet.

## Non-Goals

- No indexing or caching layer (query source data directly each time)
- No write operations (this is read-only research)
- No remote/cloud sources (local machine history only)
