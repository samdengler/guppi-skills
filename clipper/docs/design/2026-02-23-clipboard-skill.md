# Design: clipper — Copy content to clipboard without whitespace noise

**Date:** 2026-02-23
**Status:** Draft

## Problem

Claude Code indents all output per-message. When you ask Claude to write an email, a config file, or any block of text, copying it from the terminal includes unwanted leading whitespace. Manual cleanup is tedious and error-prone.

## Solution

A Claude Code skill (`/clipboard`) that copies clean content to the system clipboard. The agent writes content to a temp file and pipes it through the platform's clipboard command (`pbcopy` on macOS).

The skill is intentionally simple — no daemon, no state, no config. It's a one-shot "put this on my clipboard" action.

## Commands

### `guppi-clipper copy [--file FILE]`

Copy content to the system clipboard.

**Modes:**

1. **stdin** (primary) — read from stdin, copy to clipboard
   ```bash
   echo "hello" | guppi-clipper copy
   cat config.yaml | guppi-clipper copy
   ```

2. **file** — read from a file, copy to clipboard
   ```bash
   guppi-clipper copy --file /tmp/draft-email.txt
   ```

Both modes write to a temp file first (for debugging/recovery), then pipe to the clipboard command.

**Output:**
- Prints a confirmation with byte count and a preview (first ~80 chars)
- Prints the temp file path for recovery

```
Copied 342 bytes to clipboard
Preview: "Hi team, here's the updated config for the staging..."
Saved to /tmp/clipper-20260223-143022.txt
```

### `guppi-clipper paste`

Print clipboard contents to stdout. Useful for piping clipboard content into other commands or for the agent to read what's currently on the clipboard.

```bash
guppi-clipper paste
guppi-clipper paste | wc -l
```

### `guppi-clipper skill install` / `guppi-clipper skill show`

Standard guppi skill management commands.

## Agent Workflow (SKILL.md)

The key design decision: the **agent writes a temp file, then calls `guppi-clipper copy --file`**. This avoids shell escaping issues with piping arbitrary content through stdin in a Bash tool call.

Typical agent flow:
1. User invokes `/clipboard` (or asks "copy that to my clipboard")
2. Agent identifies the content to copy
3. Agent writes content to `/tmp/clipper-<timestamp>.txt` using the Write tool
4. Agent runs `guppi-clipper copy --file /tmp/clipper-<timestamp>.txt`
5. Agent confirms to user

## Platform Support

| Platform | Copy command | Paste command |
|----------|-------------|---------------|
| macOS | `pbcopy` | `pbpaste` |
| Linux (X11) | `xclip -selection clipboard` | `xclip -selection clipboard -o` |
| Linux (Wayland) | `wl-copy` | `wl-paste` |
| WSL | `clip.exe` | `powershell.exe Get-Clipboard` |

Auto-detect platform at runtime. Error with a clear message if the clipboard command isn't found.

## Key Implementation Details

### Temp File Naming

```
/tmp/clipper-YYYYMMDD-HHMMSS.txt
```

Use `/tmp` so the OS handles cleanup. Include timestamp for debugging — if something goes wrong, the user can find the file.

### Clipboard Detection

```python
import shutil, sys

def get_clipboard_commands() -> tuple[list[str], list[str]]:
    """Return (copy_cmd, paste_cmd) for the current platform."""
    if sys.platform == "darwin":
        return (["pbcopy"], ["pbpaste"])
    if shutil.which("wl-copy"):
        return (["wl-copy"], ["wl-paste"])
    if shutil.which("xclip"):
        return (
            ["xclip", "-selection", "clipboard"],
            ["xclip", "-selection", "clipboard", "-o"],
        )
    if shutil.which("clip.exe"):  # WSL
        return (["clip.exe"], ["powershell.exe", "-command", "Get-Clipboard"])
    raise RuntimeError("No clipboard command found")
```

### No Dependencies Beyond Typer

This skill needs zero additional dependencies. Temp files use `tempfile` (stdlib), clipboard is a subprocess call, detection uses `shutil.which` (stdlib).

## What This Skill Is NOT

- **Not a clipboard manager** — no history, no search, no sync
- **Not a formatter** — it copies exactly what you give it, no transforms
- **Not persistent** — temp files are ephemeral, clipboard is overwritten by the next copy

## Dependencies

- **typer** — CLI framework (standard for guppi skills)
- **rich** — console output (confirmation messages)

No other dependencies needed.
