# Dispatcher — Event Routing Between Skills

**Date:** 2026-03-02
**Status:** Idea

## Motivation

Skills like courier ingest content from external channels (Telegram, future Twilio, RSS). Skills like tracker store and organize items. These should be decoupled — courier shouldn't know about tracker, and tracker shouldn't know about courier.

Dispatcher sits between them: it receives items from ingest skills, applies rules to classify them, and routes them to the appropriate action (e.g., add to tracker with a tag).

## Use Cases

### 1. Shared URLs → toread

User shares an article URL from their phone to Telegram. Courier pulls it down. Dispatcher sees a URL, adds it to tracker with `toread` tag.

### 2. Ideas → idea tracker

User texts an idea to Telegram. Courier pulls it down. Dispatcher sees plain text (not a URL), adds it to tracker with `idea` tag.

### Future

- RSS feed items → tracker or notification
- Twilio SMS messages → same pipeline
- Automated spike creation for certain topics
- LLM classification for ambiguous items

## Architecture Sketch

### Pipeline Model

```
[courier receive] → stdout → [dispatcher process] → [tracker add / other actions]
```

Courier already writes messages to stdout. Dispatcher reads from stdin (or a file), applies rules, executes actions. No daemon, no bus — just a Unix pipeline.

### Rules

Rules are described in natural language in a config file, but executed as simple pattern matching (v1). Example config:

```json
{
  "rules": [
    {"match": "url", "action": "tracker add --tag toread"},
    {"match": "text", "action": "tracker add --tag idea"}
  ]
}
```

Open question: should rules be NL-described and LLM-interpreted, or structured patterns? Could start with structured and layer NL on top.

### Input Format

Dispatcher needs a structured input format from ingest skills. Courier currently outputs human-readable text. Options:

1. **JSON lines** — courier outputs `--json` format, dispatcher parses it
2. **Stdin text** — dispatcher does its own parsing (fragile)
3. **Shared file** — courier writes to a delivery dir, dispatcher reads from it

JSON lines (option 1) is cleanest. May need a `--json` flag on `courier receive`.

## Open Questions

- **Trigger model**: manual pipeline (`courier receive | dispatcher process`), cron schedule, or long-running daemon?
- **Rule format**: structured JSON patterns vs NL descriptions vs hybrid?
- **Courier output**: does courier need a `--json` output mode?
- **State**: should dispatcher track what it's already processed (dedup)?
- **Error handling**: what happens when an action fails (tracker unreachable)?
- **Should this be a skill or just a shell script?** A skill gives us SKILL.md for agent discovery and a place to grow. A shell script is simpler but harder to evolve.
- **Agent possibility**: could dispatcher itself be a Claude agent that reads incoming items and decides what to do? This would handle NL rules naturally but adds complexity and cost.

## Relationship to Other Skills

| Skill | Role |
|-------|------|
| courier | Ingest (Telegram) |
| dispatcher | Route + classify |
| tracker | Store + query |
| future: feeder? | Ingest (RSS) |
| future: texter? | Ingest (Twilio SMS) |

## Next Steps

1. Think about trigger model (manual vs auto)
2. Decide on courier `--json` output format
3. Prototype simplest possible pipeline: courier → dispatcher → tracker
4. Iterate on rule format based on real usage
