# Chrome AppleScript Automation

**Date:** 2026-02-27
**Status:** Idea

## Motivation

Chrome MCP is great but not available everywhere (e.g., work machines). Chrome's "Allow JavaScript from Apple Events" setting lets you execute arbitrary JS in tabs via AppleScript — no extensions, no MCP server, just macOS + Chrome.

## Core Mechanism

```bash
osascript -e 'tell application "Google Chrome" to execute front window's active tab javascript "document.title"'
```

## Potential Commands

- `run <js>` — execute JS in active tab, return result
- `tabs` — list open tabs (title + URL)
- `navigate <url>` — open or navigate to a URL
- `extract <selector>` — get text/HTML from a CSS selector
- `click <selector>` — click an element
- `fill <selector> <value>` — fill a form field
- `screenshot` — capture the active tab (combine with snapper?)

## Design Considerations

- **Portability**: macOS-only (AppleScript dependency), but that's the target
- **Security**: Executing arbitrary JS — should we scope or sandbox?
- **Tab targeting**: By index, URL pattern, or title match?
- **Output**: Return raw JS result or parse/format?
- **Integration with snapper**: Could delegate screenshots to snapper's CDP approach

## Open Questions

- Should this support Safari too? (Safari has similar AppleScript support)
- How to handle multi-window/multi-tab targeting?
- Should there be a "recipe" system for common automation sequences?
