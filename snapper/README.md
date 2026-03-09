# Snapper

CDP browser screenshots for capturing authenticated web pages.

**Status:** Active | **Version:** 0.1.0 | **Created:** 2026-02-12

## What it does

Snapper captures pixel-perfect PNG screenshots of authenticated web pages using Playwright's bundled Chromium with CDP (Chrome DevTools Protocol). It launches a persistent Chromium instance with named profiles, so your logins survive across sessions. You can capture Google Sheets, dashboards, admin panels — anything that requires authentication — without re-logging in every time.

## When to use it

- Capturing screenshots of pages behind authentication (Google Sheets, dashboards, admin panels)
- Automating repeatable screenshot workflows with batch configs
- Preserving the exact visual state of an already-open tab (cell selection, scroll position)
- Taking screenshots across multiple browser profiles (work, personal, project-specific)

## Quick start

```bash
# One-time setup: install Chromium and create directories
guppi-snapper init

# Launch Chromium with a named profile
guppi-snapper start

# Log into whatever sites you need in the browser window that opens...

# Capture a screenshot
guppi-snapper capture https://docs.google.com/spreadsheets/d/YOUR_ID/edit \
  --output sheet.png --wait 8

# When you're done
guppi-snapper stop
```

## What to expect

When you run `guppi-snapper start`, it:

1. Launches Playwright's bundled Chromium with CDP enabled on port 9222
2. Uses a named profile directory so cookies and logins persist
3. Loads any browser extensions found in the extensions directory
4. Saves the process state so `status` and `stop` can manage it

When you run `guppi-snapper capture`, it:

1. Connects to the running Chromium instance via CDP
2. Navigates to the URL (or finds an already-open tab with `--existing`)
3. Sets the viewport to your specified dimensions
4. Waits for the page to settle (configurable delay)
5. Takes the screenshot and optionally resizes it
6. Saves the PNG to the output path

## Commands

### `guppi-snapper init`

One-time setup. Installs Playwright's bundled Chromium and creates the directory structure for profiles and extensions. Idempotent — safe to run multiple times.

### `guppi-snapper start`

Launch Chromium with CDP enabled using a named profile. The browser window opens and stays running until you call `stop`.

- `--profile` / `-p` — profile name (default: `default`)
- `--port` — CDP port (default: `9222`)

### `guppi-snapper status`

Check if Chromium is running with CDP and show connection info, including active tabs.

- `--port` — CDP port to check (default: `9222`)

### `guppi-snapper stop`

Gracefully shut down the CDP Chromium instance and clean up the state file.

### `guppi-snapper capture <url>`

Navigate to a URL and capture a screenshot.

- `--output` / `-o` — output file path (default: `screenshot.png`)
- `--viewport` / `-v` — viewport dimensions as WxH (default: `1400x1365`)
- `--resize` / `-r` — resize the image to WxH after capture (requires ImageMagick)
- `--wait` / `-w` — seconds to wait after page load before capturing (default: `5`)
- `--existing` / `-e` — capture an already-open tab matching the URL pattern instead of navigating. Preserves cell selection, scroll position, and UI state.
- `--port` — CDP port (default: `9222`)

### `guppi-snapper batch <config_file>`

Capture multiple screenshots from a YAML config file. Supports per-capture overrides for viewport, wait, resize, and output path, with shared defaults at the top level.

### `guppi-snapper profile list`

List available profiles with name, last modified date, and size.

### `guppi-snapper profile create <name>`

Create a new empty profile directory.

### `guppi-snapper profile delete <name>`

Delete a profile directory.

- `--yes` / `-y` — skip confirmation prompt

## Configuration

Snapper stores data under XDG Base Directory paths:

| Directory | Default Path | Contents |
|-----------|-------------|----------|
| Data | `~/.local/share/guppi/snapper/` | Profiles, extensions, state |
| Config | `~/.config/guppi/snapper/` | Configuration |

Browser profiles live in the data directory under `profiles/`. Each profile maintains its own cookies, local storage, and login sessions.

Extensions placed in the `extensions/` data directory (each in a subdirectory with a `manifest.json`) are automatically loaded when Chromium starts.

## Prerequisites

- Python 3.11+
- [Playwright](https://playwright.dev/) (installed as a dependency)
- [ImageMagick](https://imagemagick.org/) (only needed for `--resize`)
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skill install`)
