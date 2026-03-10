# Shooter

Manage macOS screenshot preferences from the command line.

**Status:** Experimental | **Version:** 0.1.0 | **Created:** 2026-03-09

## What it does

Shooter lets you view and change macOS screenshot settings without opening System Settings or memorizing `defaults write` incantations. It wraps the `com.apple.screencapture` preference domain into a simple CLI — check your current save location, switch formats, or redirect screenshots to a new folder in one command.

## When to use it

- Checking where your screenshots are being saved
- Switching screenshot format (PNG, JPG, TIFF, etc.)
- Redirecting screenshots to a project-specific folder
- Quickly auditing all screenshot-related preferences

## Quick start

```bash
# See current screenshot preferences
guppi-shooter prefs

# Save screenshots to a different folder
guppi-shooter prefs --location ~/Screenshots

# Switch to JPG format
guppi-shooter prefs --format jpg
```

## What to expect

When you run `guppi-shooter prefs` with no options, it displays a table of your current screenshot settings: save location, file format, base name, shadow, date inclusion, and thumbnail behavior.

When you pass `--location` or `--format`, it writes the new value to macOS defaults and confirms the change. Multiple options can be combined in a single call.

## Commands

### `guppi-shooter prefs`

View or set macOS screenshot preferences. With no options, shows current settings.

- `--location` / `-l` — Set screenshot save location (e.g., `~/Screenshots`)
- `--format` / `-f` — Set screenshot format (`png`, `jpg`, `tiff`, `gif`, `bmp`, `pdf`)
- `--show` / `-s` — Explicitly show current preferences (default when no other options given)

## Settings reference

The `prefs` command reads and displays these `com.apple.screencapture` keys:

| Setting | Default | Description |
|---------|---------|-------------|
| `location` | `~/Desktop` | Directory where screenshots are saved |
| `type` | `png` | Image format |
| `name` | `Screenshot` | Base filename prefix |
| `disable-shadow` | `false` | Remove drop shadow from window captures |
| `include-date` | `true` | Append timestamp to filename |
| `show-thumbnail` | `true` | Show floating thumbnail after capture |

Currently `--location` and `--format` are the writable options. Other settings can be changed directly via `defaults write com.apple.screencapture <key> <value>`.

## Prerequisites

- macOS (uses `defaults` command for preference management)
- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skills install`)
