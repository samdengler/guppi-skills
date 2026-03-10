---
name: surfer
description: >
  Chrome browser automation via AppleScript JavaScript execution. Use when you
  need to interact with web pages in Chrome without requiring Chrome MCP.
allowed-tools: "Bash(guppi-surfer:*)"
version: "0.1.1"
author: "Sam Dengler"
license: "MIT"
---

# Surfer — Chrome browser automation

Automate Chrome browser interactions using macOS AppleScript's "Allow JavaScript from Apple Events" feature. A portable alternative to Chrome MCP that works anywhere you have Chrome on macOS.

## Prerequisites

Enable in Chrome: View > Developer > Allow JavaScript from Apple Events

## Commands

### `guppi-surfer run <js>`

Execute JavaScript in the active Chrome tab.

## Examples

```bash
guppi-surfer run "document.title"
guppi-surfer run "document.querySelector('h1').textContent"
```

## Skill Management

```bash
guppi-surfer skill install   # Register with guppi-cli
guppi-surfer skill show      # Display SKILL.md contents
```
