---
name: shooter
description: >
  Screenshot manager for macOS. Use when you need to view or change screenshot
  preferences like save location, format, or naming.
allowed-tools: "Bash(guppi-shooter:*)"
version: "0.1.2"
author: "Sam Dengler"
license: "MIT"
---

# Shooter — screenshot manager

Manage macOS screenshot preferences from the command line. View current settings, change save locations, switch formats, and more.

## Commands

### `guppi-shooter prefs`

View or set macOS screenshot preferences.

**Options:**
- `--location` / `-l` — Set screenshot save location
- `--format` / `-f` — Set screenshot format (png, jpg, tiff, etc.)
- `--show` / `-s` — Show current screenshot preferences (default when no options given)

## Examples

```bash
guppi-shooter prefs                        # Show current preferences
guppi-shooter prefs --location ~/Screenshots  # Change save location
guppi-shooter prefs --format jpg           # Switch to JPG format
```

## Skill Management

```bash
guppi-shooter skill install   # Register with guppi-cli
guppi-shooter skill show      # Display SKILL.md contents
```
