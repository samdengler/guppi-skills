# Clipper

Copy content to the system clipboard without whitespace noise.

**Status:** Active | **Version:** 0.1.0

## What it does

Clipper puts content on your system clipboard cleanly. When working with AI agents like Claude Code, copied output often picks up extra indentation or formatting artifacts. Clipper bypasses that by reading from a file or stdin and copying directly to the clipboard via your platform's native clipboard command. Every copy also saves a timestamped temp file in `/tmp/` so you can recover what you copied.

## When to use it

- Copying generated content (emails, configs, code) to your clipboard from an agent session
- Piping command output to the clipboard from the terminal
- Reading clipboard contents into a pipeline
- Any time you need clean, artifact-free clipboard access from the command line

## Quick start

```bash
# Copy from a file
guppi-clipper copy --file draft.txt

# Pipe content to clipboard
echo "hello world" | guppi-clipper copy

# Read what's on the clipboard
guppi-clipper paste
```

## What to expect

When you run `guppi-clipper copy`, it:

1. Reads content from the specified file or stdin
2. Copies it to the system clipboard using the platform's native command
3. Saves a timestamped backup to `/tmp/clipper-YYYYMMDD-HHMMSS.txt`
4. Prints byte count, a preview of the content, and the temp file path

If no input is provided (no `--file` and nothing on stdin), it exits with an error. Empty content produces a warning and exits without copying.

## Commands

### `guppi-clipper copy [--file FILE]`

Copy content to the system clipboard.

- `--file` / `-f` -- read content from a file instead of stdin

```bash
# From a file
guppi-clipper copy --file /tmp/clipper-email-draft.txt

# From stdin
cat config.yaml | guppi-clipper copy

# Agent workflow: write to temp file first, then copy
guppi-clipper copy --file /tmp/clipper-response.txt
```

### `guppi-clipper paste`

Print clipboard contents to stdout. Useful for piping clipboard content into other commands.

```bash
guppi-clipper paste
guppi-clipper paste | wc -l
guppi-clipper paste > saved.txt
```

## Platform support

Clipper auto-detects the clipboard command for your platform:

| Platform | Copy | Paste |
|----------|------|-------|
| macOS | `pbcopy` | `pbpaste` |
| Linux (Wayland) | `wl-copy` | `wl-paste` |
| Linux (X11) | `xclip` | `xclip` |
| WSL | `clip.exe` | `powershell.exe Get-Clipboard` |

If none of these are available, clipper exits with an error.

## Prerequisites

- Python 3.11+
- A supported clipboard command (see platform support above)
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skills install`)
