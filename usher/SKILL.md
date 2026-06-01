---
name: usher
description: >
  Rank movie showtimes by the user's format preferences and find the best
  contiguous seats by their saved seat preferences. Use when the user wants to
  find movie tickets/seats (currently Regal/regmovies.com). Booking is
  human-in-the-loop — usher proposes seats and a deep link; the user logs in and pays.
allowed-tools: "Bash(guppi-usher:*)"
version: "0.1.0"
author: "Sam Dengler"
license: "MIT"
---

# Usher — showtimes + preference-based seat ranking

Usher helps pick movie seats. Given a movie, theater, ticket count, and optional
time window, it ranks showtimes by the user's **format preferences** (Regal →
IMAX first; skip ScreenX; 4DX only for action) and finds the best **contiguous**
seats using their **saved seat preferences**.

**Never** enter payment or finalize a purchase. Propose options and the deep link;
the user completes checkout themselves.

## Prerequisites

- macOS Chrome with **View ▸ Developer ▸ Allow JavaScript from Apple Events** enabled.
- The active Chrome tab on **regmovies.com** (any page) for live seat/showtime reads —
  this is what gets past Cloudflare, using the user's own session.

## Commands

### `guppi-usher seats --theatre <code> --session <id> [--tickets N] [--screen <label> --theatre-slug <slug>]`

Fetch the seat map for a showtime and rank the best contiguous seats. With
`--screen` + `--theatre-slug`, applies the user's saved picks for that screen and
reports if they're taken. Supports `--json`.

### `guppi-usher showtimes [--json]`

List showtimes on the movie/theatre page currently open in Chrome. (Experimental:
format-per-showtime association is still being hardened.)

### `guppi-usher find <movie-slug> --theatre <code> [--tickets N] [--after HH:MM] [--action]`

End-to-end ranking. Experimental — currently guides the manual showtimes→seats flow.

### `guppi-usher prefs show [--json]` / `guppi-usher prefs path`

View saved format and seat preferences (stored under `~/.local/share/guppi/usher/`).

### `guppi-usher init`

Seed the preferences file (idempotent).

## Typical flow (Regal, today)

1. Open `https://www.regmovies.com/movies/<slug>?selected=<theatreCode>` in Chrome.
2. `guppi-usher showtimes` → pick a time; click it in Chrome (URL gains `?id=<sessionId>`).
3. `guppi-usher seats -t <code> -s <sessionId> -n <tickets> --screen "<Screen N>" --theatre-slug <slug>`.
4. Present the top options + the seat-page URL; the user logs in and pays.

## Notes

- Seat `Status`: 0 = available, 1 = taken (3/7 = accessible/blocked).
- Orientation: row A = front (screen); letters climb to the back.
- AMC (amctheatres.com) is not yet supported — planned.

## Skill Management

```bash
guppi-usher skill install   # Register with guppi-cli
guppi-usher skill show      # Display SKILL.md contents
```
