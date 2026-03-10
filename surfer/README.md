# Surfer

Chrome browser automation via AppleScript JavaScript execution.

**Status:** Experimental | **Version:** 0.1.0

## What it does

Surfer executes JavaScript in the active Google Chrome tab using macOS AppleScript. It provides a lightweight, portable way to interact with web pages from the command line or an AI agent without requiring Chrome DevTools Protocol or Chrome MCP setup.

## When to use it

- Scraping or reading content from a page already open in Chrome
- Automating simple browser interactions (clicking, filling forms, reading text)
- Extracting page data without spinning up a headless browser
- Quick browser automation on macOS when you don't need full Chrome MCP

## Current status

Surfer is currently a scaffold. The `run` command exists but is not yet implemented -- it will exit with an error. The CLI structure, skill management commands, and packaging are in place and ready for development.

## Quick start

```bash
# Install the skill
guppi skills install surfer --from ./surfer

# Once implemented, run JavaScript in the active Chrome tab
guppi-surfer run "document.title"
guppi-surfer run "document.querySelector('h1').textContent"
```

## Commands

### `guppi-surfer run <js>`

Execute JavaScript in the active Chrome tab via AppleScript.

**Arguments:**
- `js` -- JavaScript code to execute in the active tab

**Not yet implemented.** Currently exits with an error message.

### `guppi-surfer skill install`

Register this skill with guppi-cli.

### `guppi-surfer skill show`

Display the SKILL.md contents.

## Prerequisites

- macOS (AppleScript is macOS-only)
- Google Chrome with **Allow JavaScript from Apple Events** enabled (Chrome menu: View > Developer > Allow JavaScript from Apple Events)
- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skills install`)
