---
name: courier
description: >
  Telegram-based messaging for Claude workflows. Use when you need to
  send or receive messages and files between Claude Desktop and Claude Code.
allowed-tools: "Bash(guppi-courier:*)"
version: "0.1.2"
author: "Sam Dengler"
license: "MIT"
---

# Courier — Telegram-based messaging for Claude workflows

Bidirectional message queue between Claude Desktop (phone/Mac) and Claude Code via Telegram bots. Pull specs and files from Claude Desktop, push results back. Messages land in a per-bot, date-organized inbox that other skills can consume.

## Setup

```bash
guppi-courier add handoffs
```

## Commands

### `guppi-courier receive [--bot NAME] [--output DIR] [--keep]`

Receive the latest messages from a bot. Text is printed to stdout and saved as `.md` files. Documents and photos are downloaded with their original filenames. All files land in the bot's inbox (`~/.local/share/guppi/courier/inbox/<bot>/<date>/`).

**Options:**
- `--bot` / `-b` — bot name (default: the default bot)
- `--output` / `-o` — override inbox directory for this receive
- `--keep` — don't acknowledge messages (they'll appear again)

### `guppi-courier send [MESSAGE] [--bot NAME] [--file PATH]`

Send a message or file via the bot.

**Options:**
- `--bot` / `-b` — bot name (default: the default bot)
- `--file` / `-f` — send a file as a document

### `guppi-courier inbox [BOT] [--today]`

Print the inbox path for a bot. Other skills use this to discover where messages land.

```bash
inbox=$(guppi-courier inbox handoffs --today)
```

### `guppi-courier peek [--bot NAME]`

Preview waiting messages without acknowledging.

### `guppi-courier bots`

List registered bots and their status.

### `guppi-courier add NAME [--bot-name TELEGRAM_NAME] [--default]`

Register a new bot. Prompts for the token, verifies it, and checks for a chat ID.

### `guppi-courier remove NAME`

Remove a bot from the registry.

## Skill Management

```bash
guppi-courier skill install   # Register with guppi-cli
guppi-courier skill show      # Display SKILL.md contents
```
