# Usher

Rank movie showtimes by format and find the best contiguous seats by your saved preferences.

**Status:** Experimental | **Version:** 0.1.0

## What it does

You give usher a movie, theater, ticket count, and (optionally) a time window. It
ranks the showtimes by **your format preferences** and finds the best **block of
seats next to each other** using **your saved seat preferences** for that
auditorium. Then it shows you the top options and a link to the seat page —
**you log in and pay.** Usher never enters payment or completes a purchase.

Today it supports **Regal** (regmovies.com). AMC is planned.

## How it works

regmovies.com sits behind Cloudflare bot protection, so usher reads showtimes and
seat maps **through your own Chrome session** (via a small AppleScript bridge)
rather than a standalone HTTP client. The active Chrome tab needs to be on
regmovies.com.

Preferences:
- **Format:** Regal → IMAX first, then RPX, then Standard; **ScreenX skipped**;
  **4DX only for action movies**. AMC → Dolby first.
- **Seats:** contiguous only; ranked by closeness to row center; uses your saved
  per-screen picks when available, else the nearest match.

## Prerequisites

- macOS + Google Chrome with **View ▸ Developer ▸ Allow JavaScript from Apple Events**
- Python 3.11+, [uv](https://docs.astral.sh/uv/)
- For seat/showtime reads: the active Chrome tab on regmovies.com

## Quick start

```bash
guppi skills install usher --from ./usher
guppi-usher init                 # seed your preferences
guppi-usher prefs show           # review them
```

Typical Regal flow:

```bash
# 1. Open the movie at your theater in Chrome:
#    https://www.regmovies.com/movies/<slug>?selected=<theatreCode>
guppi-usher showtimes            # list times on that page
# 2. Click your chosen showtime in Chrome (URL gains ?id=<sessionId>)
guppi-usher seats --theatre 1346 --session <sessionId> --tickets 2 \
  --screen "Screen 9" --theatre-slug regal-atlantic-station
```

## Commands

| Command | Purpose |
|---------|---------|
| `init` | Seed the preferences file (idempotent) |
| `seats -t <code> -s <id> [-n N] [--screen L --theatre-slug S]` | Rank best contiguous seats for a showtime (`--json`) |
| `showtimes` | List showtimes on the current Chrome page (`--json`, experimental) |
| `find <slug> -t <code> [-n N] [--after HH:MM] [--action]` | End-to-end ranking (experimental) |
| `prefs show` / `prefs path` | View saved preferences |
| `skill install` / `skill show` | Agent integration |

## Preferences

Stored as JSON at `~/.local/share/guppi/usher/preferences.json`. Seeded with the
owner's Regal Atlantic Station and AMC Madison Yards preferences; anchor seat
picks on the chain's own "Screen N" label.

## Status / roadmap

- ✅ Seat-map fetch + contiguous-seat ranking + saved-pick matching (Regal)
- ✅ Format ranking rules (IMAX-first, skip ScreenX, 4DX-action-only, Dolby for AMC)
- 🚧 Live showtime + format extraction for fully automatic `find`
- 🚧 Refactor the Chrome bridge onto the `surfer` skill
- 📋 AMC (amctheatres.com) support

## Disclaimer

Personal automation. Use at your own risk. Booking is always human-in-the-loop.
