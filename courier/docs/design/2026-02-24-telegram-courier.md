# Courier — Telegram-based messaging for Claude workflows

## Problem

You design and explore ideas in Claude Desktop — on your phone or Mac. When a task needs execution or a file needs to land on your dev machine, there's no clean bridge. And when Claude Code finishes work, there's no way to send results back to your phone. Copy-paste loses formatting, AirDrop requires both devices awake, and iCloud sync is slow and unreliable for ad-hoc handoffs.

## Solution

Use Telegram bots as a bidirectional message queue between Claude Desktop and Claude Code.

```
┌─────────────────┐              ┌──────────────┐              ┌──────────────┐
│ Claude Desktop  │  ──share──▶  │   Telegram   │  ◀──send──  │ Claude Code  │
│ (phone / mac)   │  ◀─notify─  │   Bot(s)     │  ─receive─▶ │ guppi-courier│
└─────────────────┘              └──────────────┘              └──────────────┘
```

- **receive** — fetch messages sent to the bot (Claude Desktop → Claude Code)
- **send** — send messages/files via the bot (Claude Code → Claude Desktop)

## Design

### Multiple named bots

Different bots for different purposes. Each bot has a name and a token.

Bot naming convention: `dengler_<person>_<topic>_bot`

Examples:
- `dengler_sam_handoffs_bot` — Claude Desktop → Claude Code bridge
- `dengler_sam_openclaw_bot` — Agent gateway
- `dengler_family_coord_bot` — Family coordination

### Bot registry (config)

Bot settings live in `~/.config/guppi/courier/config.json`:

```json
{
  "default": "handoffs",
  "bots": {
    "handoffs": {
      "name": "dengler_sam_handoffs_bot"
    },
    "openclaw": {
      "name": "dengler_sam_openclaw_bot"
    }
  }
}
```

- Tokens are stored via `guppi-locker` — never in config files or env vars
- `default` sets which bot commands use when no `--bot` is specified
- `guppi-courier add` stores the token in locker and registers the bot in config

### Chat ID and offset tracking (state)

Per-bot state lives in `~/.local/state/guppi/courier/`:

```
~/.local/state/guppi/courier/offsets/handoffs    # contains: 123456789
~/.local/state/guppi/courier/offsets/openclaw    # contains: 987654321
~/.local/state/guppi/courier/chat_ids/handoffs   # contains: 12345678
```

- **Offsets** — Telegram `getUpdates` offset, one plain integer per bot. Tracks which messages have been consumed.
- **Chat IDs** — learned from the first `getUpdates` response. Required for `send` (sending messages back). One integer per bot.

One file per bot per concern. No JSON, just plain integers. Avoids read-modify-write collisions if multiple bots are used concurrently.

### Secrets via guppi-locker

Courier uses `guppi-locker` for all token storage.

```bash
# Courier stores tokens under the "courier" service
guppi-locker set courier handoffs --value "bot-token-here"
guppi-locker get courier handoffs

# List all courier tokens
guppi-locker list courier
```

At runtime, courier calls `guppi-locker get courier <bot-name>` via subprocess to retrieve the token. No tokens touch the filesystem, env vars, or shell config.

### Telegram Bot API

All interaction uses the HTTP Bot API — no third-party libraries needed.

```
# Receiving
GET https://api.telegram.org/bot<token>/getUpdates?offset=<update_id+1>
GET https://api.telegram.org/bot<token>/getFile?file_id=<file_id>
GET https://api.telegram.org/file/bot<token>/<file_path>

# Sending
POST https://api.telegram.org/bot<token>/sendMessage
POST https://api.telegram.org/bot<token>/sendDocument
```

- `getUpdates` returns messages (text, documents, photos) and provides the `chat_id`
- `sendMessage` / `sendDocument` send text or files back to the chat
- Bots can't initiate chats — the user must message the bot first (gives us the `chat_id`)

Python stdlib `urllib.request` handles all HTTP — no `requests` or `httpx` needed.

### Inbox (data)

Pulled messages land in a per-bot, date-organized inbox under `~/.local/share/guppi/courier/inbox/`:

```
~/.local/share/guppi/courier/inbox/handoffs/
  2026-02-24/
    091500.md          # text message at 09:15:00
    091532.md          # another text at 09:15:32
    budget.xlsx        # document (original filename)
    budget (1).xlsx    # collision gets macOS-style suffix
    photo.jpg          # photo
  2026-02-25/
    ...
```

- Text messages → `<HHMMSS>.md` (timestamp from Telegram)
- Documents/photos → original filename
- Collisions → `(1)`, `(2)`, etc.
- `--output` overrides the inbox for ad-hoc receives
- Other skills discover the inbox path via `guppi-courier inbox <bot>`

### What gets shared

**Pulling (inbound):**

| Type | What courier does |
|------|-------------------|
| **Text** | Print to stdout AND save as `<HHMMSS>.md` in inbox |
| **Document** | Download to inbox (original filename) |
| **Photo** | Download highest-res version to inbox |
| **URL in text** | Fetch the URL content and print to stdout |

**Pushing (outbound):**

| Input | What courier sends |
|-------|-------------------|
| **Text argument** | `sendMessage` with the text |
| **Stdin pipe** | `sendMessage` with piped content |
| **`--file` path** | `sendDocument` with the file |

## Commands

### `guppi-courier receive [--bot NAME] [--output DIR] [--keep]`

Fetch the latest message(s) from a bot.

- `--bot` / `-b` — bot name from registry (default: the `default` bot)
- `--output` / `-o` — directory for downloaded files (default: `.`)
- `--keep` — don't acknowledge messages (they'll appear again on next receive)
- Prints text content to stdout, downloads files to output dir
- By default, acknowledges messages after successful receive (updates offset)
- Learns and persists `chat_id` from the response (enables `send`)

```bash
# Pull latest from default bot
guppi-courier receive

# Pull from a specific bot
guppi-courier receive --bot openclaw

# Download files to a specific directory
guppi-courier receive --output ./handoffs/
```

### `guppi-courier send [MESSAGE] [--bot NAME] [--file PATH]`

Send a message or file via the bot.

- `MESSAGE` — text to send (reads from stdin if omitted and no `--file`)
- `--bot` / `-b` — bot name from registry (default: the `default` bot)
- `--file` / `-f` — send a file as a document
- If no `chat_id` on file, does a quick `getUpdates` to learn it before sending

```bash
# Send text
guppi-courier send "Build complete — 3 tests passing"

# Pipe content
cat results.json | guppi-courier send --bot handoffs

# Send a file
guppi-courier send --file ./report.pdf
```

### `guppi-courier inbox [BOT] [--today]`

Print the inbox path for a bot. Other skills use this to discover where messages land.

- `BOT` — bot name (default: the `default` bot)
- `--today` — append today's date subdirectory

```bash
$ guppi-courier inbox handoffs
/Users/sam/.local/share/guppi/courier/inbox/handoffs

$ guppi-courier inbox handoffs --today
/Users/sam/.local/share/guppi/courier/inbox/handoffs/2026-02-24

# Other skills use it to discover the inbox:
inbox=$(guppi-courier inbox handoffs --today)
```

### `guppi-courier peek [--bot NAME]`

Show what's waiting without acknowledging. Preview of what `receive` would fetch.

### `guppi-courier bots`

List registered bots and their status. Checks token (via locker) and chat_id (via state).

```bash
$ guppi-courier bots
  Bot         Status
  handoffs    ready (default)
  openclaw    needs first message — open @dengler_sam_openclaw_bot in Telegram
  research    token missing
```

### `guppi-courier add NAME [--bot-name TELEGRAM_NAME] [--default]`

Register a new bot. Prompts interactively for the token (never passed as a CLI arg — avoids shell history leaks). After storing the token:

1. Calls `getMe` to verify the token and learn the bot's username
2. Calls `getUpdates` to check for existing messages
3. If messages exist → saves the `chat_id`, bot is fully ready
4. If no messages → saves the bot but warns:
   `No messages yet. Send a message to @bot_username in Telegram, then run: guppi-courier add handoffs`

Re-running `add` for an existing bot is safe — it re-checks for the `chat_id` without re-prompting for the token.

```bash
$ guppi-courier add handoffs
Token: ****
Verified: @dengler_sam_handoffs_bot
Chat ID learned — bot is ready
Bot 'handoffs' added (default)

$ guppi-courier add openclaw --default
Token: ****
Verified: @dengler_sam_openclaw_bot
No messages yet. Send a message to @dengler_sam_openclaw_bot in Telegram, then run:
  guppi-courier add openclaw
Bot 'openclaw' added (default, needs first message)
```

### `guppi-courier remove NAME`

Remove a bot from the registry and delete its token from locker.

## File layout

```
~/.config/guppi/courier/config.json                    # Bot registry (settings)
~/.local/share/guppi/courier/inbox/<bot>/<date>/       # Inbox (received messages/files)
~/.local/state/guppi/courier/offsets/<bot>              # Update offset per bot (plain integer)
~/.local/state/guppi/courier/chat_ids/<bot>             # Chat ID per bot (plain integer)
```

Tokens live in locker, not on the filesystem.

## Dependencies

- **typer** — CLI framework (standard guppi dependency)
- **guppi-locker** — secret storage (called as subprocess)
- **No other dependencies** — `urllib.request` + `json` for Telegram API, config, and state

## Open questions

1. **Artifact URL fetching** — Claude Desktop artifact URLs may require auth or may be ephemeral. Need to test. If they're not fetchable, text content of the message is still useful.
2. **Slash command** — Should courier also install a `/courier` slash command for Claude Code, or is `guppi-courier receive` sufficient on its own?
