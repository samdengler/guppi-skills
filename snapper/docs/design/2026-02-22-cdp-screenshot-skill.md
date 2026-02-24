# Design: snapper — CDP Browser Screenshot Skill

**Date:** 2026-02-22
**Status:** Draft

## Problem

Capturing high-quality screenshots of authenticated web pages (Google Sheets, admin dashboards, etc.) for use in documentation, tutorial videos, and guides is painful:

- **html2canvas** is blocked by CSP on many sites (Google Sheets uses Trusted Types)
- **macOS `screencapture`** captures window chrome (tab bar, address bar, shadow) requiring fragile crop offsets that vary between captures
- **Browser extension screenshots** are JPEG, 1x resolution, and hard to save to disk
- **Playwright `launch()`** creates a new browser without existing auth sessions
- **Manual screenshots** (Cmd+Shift+4) aren't repeatable or scriptable

## Solution

Use **Playwright's bundled Chromium** (not the user's Chrome) to avoid interfering with daily browsing. Snapper launches a separate Chromium instance with `--remote-debugging-port` and connects via `connectOverCDP()` for programmatic control — navigate, interact, wait, and screenshot at exact viewport dimensions.

## Core Concept: Named Chromium Profiles

Chromium requires `--user-data-dir` (a non-default profile directory) to enable CDP. Different directories = different login states. Snapper manages these as **named profiles**:

```
~/.local/share/guppi/snapper/
├── profiles/
│   ├── default/          # Reusable — keeps Google, GitHub logins
│   ├── fresh/            # Always clean
│   └── project-foo/      # Project-specific auth state
└── extensions/
    └── claude/           # Unpacked browser extensions
```

Logins persist across Chromium restarts within the same profile. User logs in once, reuses forever.

## Directory Layout (XDG Base Directory)

Snapper follows the XDG Base Directory Specification, under a shared `guppi` namespace:

| Purpose | Path | Env Override |
|---------|------|-------------|
| Configuration | `~/.config/guppi/snapper/config.toml` | `XDG_CONFIG_HOME` |
| Data (profiles, extensions) | `~/.local/share/guppi/snapper/` | `XDG_DATA_HOME` |

Config file (`config.toml`) stores defaults like port, extensions to load, etc. Profile data and extensions are persistent data, not configuration.

## Browser Extensions

New profiles automatically load extensions from `~/.local/share/guppi/snapper/extensions/`. Each subdirectory is an unpacked extension passed via Chromium's `--load-extension` flag at launch.

**Setup (one-time):** Copy the Claude extension from your Chrome profile:

```bash
# Find the extension ID in chrome://extensions, then:
cp -r ~/Library/Application\ Support/Google/Chrome/Default/Extensions/<ext-id>/<version>/ \
  ~/.local/share/guppi/snapper/extensions/claude/
```

All extensions in the directory are loaded for every profile — no per-profile configuration needed.

## Commands

### `guppi-snapper start [--profile NAME] [--port PORT]`

Launch Chromium with CDP enabled using a named profile. Loads all extensions from the extensions directory.

- `--profile` defaults to `default`
- `--port` defaults to `9222`
- Creates the profile directory if it doesn't exist
- Loads extensions from `~/.local/share/guppi/snapper/extensions/`
- Errors if Chromium is already running on that port
- Prints connection info on success

```bash
guppi-snapper start                      # default profile, port 9222
guppi-snapper start --profile fresh      # clean profile
guppi-snapper start --profile myproject  # project-specific logins
```

### `guppi-snapper status`

Check if Chromium is running with CDP and show connection info.

```bash
guppi-snapper status
# Chromium CDP active on port 9222
# Profile: default
# Tabs: 3 (google.com, localhost:8888, docs.google.com/...)
```

### `guppi-snapper capture URL [--output FILE] [--viewport WxH] [--resize WxH] [--wait SECONDS] [--existing]`

Navigate to a URL and capture a screenshot.

- `--output` defaults to `screenshot.png`
- `--viewport` defaults to `1400x1365`
- `--resize` — optional target dimensions. If set, proportionally resize the captured image (e.g., `--resize 1120x1092` after capturing at `1400x1365`). Viewport and resize must share the same aspect ratio.
- `--wait` defaults to `5` (seconds after load to let SPAs render)
- `--existing` — capture an already-open tab matching the URL pattern instead of navigating a new page. Preserves cell selection, scroll position, and UI state. Essential for canvas-based apps like Google Sheets.
- Uses `browser.contexts()[0]` to reuse existing auth
- Uses `waitUntil: 'load'` (not `networkidle` — SPAs never go idle)

```bash
# Navigate to URL and capture
guppi-snapper capture https://docs.google.com/spreadsheets/d/ID/edit \
  --output step-2-sheet.png \
  --viewport 1400x1365 \
  --resize 1120x1092 \
  --wait 8

# Capture existing tab (preserves cell selection state)
guppi-snapper capture spreadsheets \
  --existing \
  --output step-3-sheet-selected.png \
  --viewport 1400x1365 \
  --resize 1120x1092 \
  --wait 3
```

### `guppi-snapper batch CONFIG_FILE`

Capture multiple screenshots from a YAML/JSON config file. Enables repeatable capture pipelines.

```yaml
# screenshots.yaml
viewport: 1400x1365
resize: 1120x1092
wait: 8
output_dir: ./public/screenshots

captures:
  - url: https://docs.google.com/spreadsheets/d/ID/edit
    output: step-2-sheet-pending.png
    wait: 8

  - url: spreadsheets
    existing: true        # capture already-open tab (preserves cell state)
    output: step-3-sheet-selected.png
    wait: 3

  - url: http://localhost:8888/admin
    output: step-1-dashboard.png
    viewport: 1120x1092   # override — no resize needed for localhost
    resize: null
```

```bash
guppi-snapper batch screenshots.yaml
```

### `guppi-snapper profile list`

List available profiles with status (exists, has logins, last used).

### `guppi-snapper profile create NAME`

Create a new empty profile directory.

### `guppi-snapper profile delete NAME`

Delete a profile directory (with confirmation).

### `guppi-snapper stop`

Gracefully shut down the CDP Chromium instance.

## Key Implementation Details

### Playwright CDP Connection

Two modes: **navigate to URL** (new page) or **capture existing tab** (reuse page state).

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
    context = browser.contexts[0]  # MUST reuse existing context for auth

    # Mode 1: Navigate to URL (new page)
    page = context.new_page()
    page.set_viewport_size({"width": width, "height": height})
    page.goto(url, wait_until="load", timeout=60000)
    page.wait_for_timeout(wait_ms)
    page.screenshot(path=output, type="png")

    # Mode 2: Capture existing tab (preserves cell selection, scroll, UI state)
    page = next(p for p in context.pages if "spreadsheets" in p.url)
    page.set_viewport_size({"width": width, "height": height})
    page.wait_for_timeout(wait_ms)  # let viewport change settle
    page.screenshot(path=output, type="png")
```

Mode 2 is critical for canvas-based apps like Google Sheets where cell selection and scroll position can't be set via Playwright DOM interaction.

### Proportional Capture and Resize

When the target output size differs from the capture viewport, capture at a proportional scale and resize with ImageMagick:

```bash
# Target: 1120x1092. Capture at 1.25x → 1400x1365
guppi-snapper capture URL --viewport 1400x1365 --output raw.png

# Resize proportionally (NEVER use ! flag — it squishes)
magick raw.png -resize 1120x1092 final.png
```

The key: both dimensions must scale by the **same factor** (1400/1120 = 1365/1092 = 1.25). ImageMagick's `-resize WxH` (without `!`) preserves aspect ratio automatically.

### Finding Element Coordinates with ImageMagick

Instead of guessing button positions in screenshots, scan for color signatures:

```bash
# Find orange button center by scanning for its color
for y in $(seq 280 5 400); do
  for x in $(seq 550 20 800); do
    color=$(magick screenshot.png -crop 1x1+${x}+${y} \
      -format '%[fx:int(255*r)],%[fx:int(255*g)],%[fx:int(255*b)]' info:)
    r=$(echo $color | cut -d, -f1)
    g=$(echo $color | cut -d, -f2)
    b=$(echo $color | cut -d, -f3)
    if [ "$r" -gt 180 ] && [ "$g" -lt 150 ] && [ "$b" -lt 100 ]; then
      echo "ORANGE at ($x,$y)"
    fi
  done
done
# Average min/max x,y to find button center
```

This is essential for Remotion compositions — cursor animations need pixel-accurate targets.

### Gotchas

1. **Always `browser.contexts[0]`** — `browser.new_context()` creates a fresh context without cookies/auth
2. **Reuse existing tabs when possible** — `context.pages` returns all open tabs. Use `next(p for p in context.pages if "keyword" in p.url)` to find a specific tab. `context.new_page()` creates a separate tab that won't have the same cell selection, scroll position, or UI state.
3. **`wait_until='load'`** not `'networkidle'` — Google Sheets and SPAs never stop making requests
4. **Extra wait after load** — SPAs need time to render dynamic content after the load event
5. **Chromium launch requires `--user-data-dir`** — Chromium refuses `--remote-debugging-port` with the default profile. Error: "DevTools remote debugging requires a non-default data directory"
6. **`process.exit()`** — `browser.close()` shuts down Chromium entirely. Just disconnect or exit the script.
7. **Viewport width** — Must be wide enough to show all target content (e.g., 1400px for Google Sheets to show all columns)
8. **Extensions via `--load-extension`** — Only works with unpacked extensions (directories, not .crx files). Extensions are loaded at launch, not dynamically.
9. **Canvas-based apps (Google Sheets)** — DOM selectors don't work for cell interaction. Use a browser extension or CDP Input domain for clicks/typing, then Playwright for the screenshot capture only.

### Dependencies

- **playwright** — CDP connection, browser control, screenshots
- **typer** — CLI framework (standard for guppi skills)
- **rich** — console output
- **pyyaml** — batch config parsing

Playwright is a heavier dependency than typical for guppi skills (which prefer stdlib). But it's the right tool — it handles CDP connection, page lifecycle, viewport control, and PNG screenshot capture reliably. No need to reimplement this with raw CDP.

Snapper uses Playwright's bundled Chromium (`playwright install chromium`) rather than the user's Chrome, to avoid interfering with daily browsing. The `start` command launches this Chromium with `--remote-debugging-port` and `--user-data-dir`, then `capture` connects via CDP.

## Integration with Remotion (and similar tools)

Snapper captures screenshots. Downstream tools compose them into videos/docs:

```bash
# Capture all screenshots
guppi-snapper batch admin-guide-screenshots.yaml

# Render video with Remotion
cd admin-guide-video && npm run render
```

This separates concerns: snapper handles the hard part (authenticated, high-quality capture), and the composition tool (Remotion, FFmpeg, whatever) handles animation and rendering.

## Future Ideas

- **`--scale 2`** — 2x device scale factor for Retina-quality captures (needs CDP Emulation.setDeviceMetricsOverride or new context with cookie transfer)
- **`--actions`** — Click, type, scroll before capturing (for capturing specific UI states)
- **`--selector`** — Wait for a specific CSS selector before capturing
- **`--clip x,y,w,h`** — Capture a region of the viewport
- **`--format jpeg`** — JPEG output with quality control
- **`--diff`** — Compare new screenshot against previous version
- **Profile import/export** — Share auth profiles across machines (cookies only, not passwords)
