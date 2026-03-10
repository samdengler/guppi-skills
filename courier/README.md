# Courier

Telegram-based messaging for Claude workflows.

**Status:** Active | **Version:** 0.1.0 | **Created:** 2026-03-09

## What it does

Courier turns Telegram bots into a bidirectional message queue between Claude Desktop (phone or Mac) and Claude Code. You register a Telegram bot, send it messages or files from your phone, and pull them into your terminal. You can also push results back. Messages land in a per-bot, date-organized inbox that other skills can consume.

Bot tokens are stored securely via guppi-locker. Message offsets and chat IDs are tracked automatically so you only see new messages each time.

## When to use it

- Handing off a task from Claude Desktop to Claude Code (specs, screenshots, files)
- Sending results from a Claude Code session back to your phone
- Piping output from one skill into a Telegram message
- Bridging mobile and terminal workflows without email or shared drives

## Quick start

```bash
# Register a bot (prompts for the token from @BotFather)
guppi-courier add handoffs

# Send your bot a message in Telegram, then receive it
guppi-courier receive

# Send a message back
guppi-courier send "Here are the results"

# Send a file
guppi-courier send --file ./report.pdf
```

## What to expect

### Adding a bot

When you run `guppi-courier add handoffs`, it:

1. Prompts for the bot token (from Telegram's @BotFather)
2. Verifies the token against the Telegram API
3. Stores the token securely in guppi-locker
4. Checks for a chat ID (learned from your first message to the bot)

If you haven't messaged the bot yet, it tells you to open it in Telegram and send any message, then re-run `add` to learn the chat ID.

### Receiving messages

When you run `guppi-courier receive`, it:

1. Fetches unread messages from the Telegram bot API
2. Prints text messages to stdout
3. Saves text as `.md` files and downloads documents/photos
4. Stores everything in the inbox: `~/.local/share/guppi/courier/inbox/<bot>/<date>/`
5. Acknowledges messages so they don't appear again

### Sending messages

You can send three ways:
- `guppi-courier send "message text"` -- pass text as an argument
- `echo "piped text" | guppi-courier send` -- pipe from stdin
- `guppi-courier send --file ./path.pdf` -- send a file as a document (with optional caption)

## Commands

### `guppi-courier add <name>`

Register a new Telegram bot. Prompts for the token and verifies it.

- `--bot-name` -- Telegram bot username (auto-detected from token if omitted)
- `--default` -- set as the default bot

### `guppi-courier remove <name>`

Remove a bot from the registry. Deletes the token, offset, and chat ID.

### `guppi-courier bots`

List registered bots with their status: ready, token missing, or needs first message.

### `guppi-courier receive`

Receive the latest messages from a bot. Text is printed to stdout. Text, documents, and photos are saved to the inbox.

- `--bot` / `-b` -- bot name (default: the default bot)
- `--output` / `-o` -- override inbox directory for this receive
- `--keep` -- don't acknowledge messages (they'll appear again next time)

### `guppi-courier send [message]`

Send a message or file via the bot. Reads from stdin if no message argument is provided.

- `--bot` / `-b` -- bot name (default: the default bot)
- `--file` / `-f` -- send a file as a document

### `guppi-courier peek`

Preview waiting messages without acknowledging them. Useful for checking what's queued before committing to a receive.

- `--bot` / `-b` -- bot name (default: the default bot)

### `guppi-courier inbox [bot]`

Print the inbox path for a bot. Designed for shell composition with other tools.

- `--today` -- print today's dated subdirectory instead of the bot root

```bash
inbox=$(guppi-courier inbox handoffs --today)
ls "$inbox"
```

## Configuration

Courier uses XDG directories for all storage:

| Path | Purpose |
|------|---------|
| `~/.config/guppi/courier/config.json` | Bot registry (names, defaults) |
| `~/.local/share/guppi/courier/inbox/<bot>/<date>/` | Received messages and files |
| `~/.local/state/guppi/courier/offsets/` | Message offsets per bot |
| `~/.local/state/guppi/courier/chat_ids/` | Chat IDs per bot |

Bot tokens are stored in guppi-locker (not in config files).

## Prerequisites

- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skills install`)
- [guppi-locker](../locker/) (for secure token storage)
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
