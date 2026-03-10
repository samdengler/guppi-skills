---
name: clipper
description: >
  Copy content to the system clipboard without whitespace noise.
  Use when you need to copy generated content (emails, configs, code) to the user's clipboard cleanly.
allowed-tools: "Bash(guppi-clipper:*)"
version: "0.1.1"
author: "Sam Dengler"
license: "MIT"
---

# Clipper — Clean clipboard copy

Copies content to the system clipboard, bypassing the indentation that Claude Code adds to output. Write content to a temp file, then use `guppi-clipper copy --file` to put it on the clipboard.

## Commands

### `guppi-clipper copy [--file FILE]`

Copy content to the system clipboard.

**Options:**
- `--file` / `-f` — read content from a file (recommended for agent use)

**Agent workflow:**
1. Write the content to `/tmp/clipper-<context>.txt` using the Write tool
2. Run `guppi-clipper copy --file /tmp/clipper-<context>.txt`

**Stdin workflow:**
```bash
echo "hello" | guppi-clipper copy
cat config.yaml | guppi-clipper copy
```

### `guppi-clipper paste`

Print clipboard contents to stdout.

```bash
guppi-clipper paste
guppi-clipper paste | wc -l
```

## Examples

```bash
# Agent: write content to temp file, then copy
guppi-clipper copy --file /tmp/clipper-email-draft.txt

# Pipe content directly
echo "clean text" | guppi-clipper copy

# Read clipboard
guppi-clipper paste
```

## Skill Management

```bash
guppi-clipper skill install   # Register with guppi-cli
guppi-clipper skill show      # Display SKILL.md contents
```
