---
name: courier
description: >
  Telegram-based messaging for Claude workflows. Use when you need to
  send or receive messages and files between Claude Desktop and Claude Code.
allowed-tools: "Bash(guppi-courier:*)"
version: "0.1.0"
author: "Sam Dengler"
license: "MIT"
---

# Courier — Telegram-based messaging for Claude workflows

Bidirectional message queue between Claude Desktop (phone/Mac) and Claude Code via Telegram bots. Pull specs and files from Claude Desktop, push results back.

## Setup

```bash
guppi-courier add handoffs
```

## Commands

### `guppi-courier pull [--bot NAME] [--output DIR] [--keep]`

Fetch the latest messages from a bot.

### `guppi-courier push [MESSAGE] [--bot NAME] [--file PATH]`

Send a message or file via the bot.

### `guppi-courier peek [--bot NAME]`

Preview waiting messages without acknowledging.

### `guppi-courier bots`

List registered bots and their status.

### `guppi-courier add NAME [--bot-name TELEGRAM_NAME] [--default]`

Register a new bot.

### `guppi-courier remove NAME`

Remove a bot from the registry.

## Skill Management

```bash
guppi-courier skill install   # Register with guppi-cli
guppi-courier skill show      # Display SKILL.md contents
```
