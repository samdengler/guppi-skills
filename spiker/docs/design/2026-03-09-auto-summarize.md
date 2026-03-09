# Auto-Summarize for Spiker

**Date:** 2026-03-09
**Status:** Approved

## Problem

AGENTS.md instructs agents to call `guppi-spiker describe` at session end, but agents routinely ignore this. Result: most spikes have no summaries, making `guppi-spiker list` useless for recall.

The `describe` command works fine as a primitive — the gap is in *triggering* it reliably.

## Solution

A three-layer approach where each layer is independent and optional:

| Layer | What | When |
|-------|------|------|
| `describe` | Manual setter (exists today) | User writes their own summary |
| `summarize` | New command — reads transcript, calls Claude to generate summary | User or hook triggers it |
| SessionEnd hook | Calls `summarize` automatically | Claude Code session ends in a spike directory |

### Layer 1: `describe` (no changes)

```bash
guppi-spiker describe warm-sage-parrot "explored Claude API streaming patterns"
```

Stays as-is. Any summarization mechanism ultimately calls this.

### Layer 2: `summarize` command (new)

```bash
guppi-spiker summarize --from-hook  # called by SessionEnd hook (reads stdin)
```

Reads a Claude Code session transcript, sends it to Claude Haiku for a one-line summary, then stores it via `describe` internally. Only invoked via the SessionEnd hook — not intended for manual use. For manual summaries, use `describe` directly.

**`--from-hook` flag (required):**
- Reads hook input from stdin (JSON with `session_id`, `transcript_path`, `cwd`)
- Uses `cwd` to detect if we're inside a spike directory
- Uses `transcript_path` for the transcript
- Silently exits if not in a spike directory (no error, no output)
- Silently exits if spike already has a summary (idempotent)

**Behavior:**
1. Parse hook input from stdin
2. Check if `cwd` is inside a spike directory; exit silently if not
3. Resolve the spike from the directory name
4. Check if spike already has a summary; exit silently if so
5. Load the transcript JSONL file
6. Extract user and assistant messages (filter out tool calls, system messages)
7. Truncate to a reasonable context window (last N messages or last ~4000 tokens)
8. Call `claude -p --model haiku --no-session-persistence` with the transcript text as input
9. Store the result via the same path as `describe`

**Auth:** Uses the `claude` CLI directly — inherits whatever auth Claude Code already has (OAuth, API key, proxy). No separate API key needed.

**Model:** Haiku via `--model haiku` — fast, cheap, more than capable for one-line summaries.

### Layer 3: SessionEnd hook (new)

A Claude Code hook that fires when a session ends. The `summarize` command handles detecting whether we're in a spike directory.

**Configuration:** Added to the user's `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "guppi-spiker summarize --from-hook"
          }
        ]
      }
    ]
  }
}
```

**Hook input (provided by Claude Code via stdin):**
```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/sam/.claude/projects/.../abc123.jsonl",
  "cwd": "/Users/sam/.spikes/2026-03-05-warm-sage-parrot",
  "hook_event_name": "SessionEnd"
}
```

## Dependencies

No new dependencies. Uses the `claude` CLI (already installed if you're using Claude Code) via `subprocess.run`.

## Transcript Parsing

Claude Code transcripts are JSONL files. Each line is a JSON object. Relevant fields:

- Messages with `role: "user"` and `role: "assistant"` contain the conversation
- Tool calls and results can be skipped for summarization
- Extract text content, join into a condensed transcript
- Truncate to last ~4000 tokens to stay well within Haiku's context and keep costs minimal

## Edge Cases

- **`claude` CLI not found** — silent exit
- **Not in a spike directory** — silent exit
- **Spike already has a summary** — silent exit (don't overwrite)
- **Empty/short transcript** — generate best-effort summary or skip
- **API failure** — silent exit; spike just won't get a summary
- **`--from-hook` without stdin** — silent exit

All failures are silent because this runs as a hook — it should never block session teardown or produce unexpected output.

## Resolved Decisions

- **No manual mode for `summarize`** — use `describe` for manual summaries, `summarize` is hook-only
- **No `--model` flag** — Haiku is the right default; add later if needed
- **No auto-tagging** — summary-only for v1; tags are more subjective
- **No `--transcript` flag** — hook provides transcript_path via stdin; no need for manual path
