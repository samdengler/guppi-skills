# Tracker on Beads for Claude Code and Cowork

**Date:** 2026-09-12
**Status:** Implemented (v1.0.0)
**Supersedes:** 2026-03-02-tracker-with-guppi-beads.md, 2026-03-02-alfred-quick-capture.md

The full design document, with diagrams and the decision table, is an HTML
file in the Claude project folder for the tracker
(`Documents/Claude/Projects/Tracker/2026-09-12-work-item-tracker-on-beads.html`).
This note records what was decided and what was verified.

## Decisions

- Beads stays the store. It already has epics, typed dependencies, and
  `bd ready`, which is the parallel frontier the tracker needs.
- The Python wrapper is retired. Agents and humans call `bd` through a shim.
- The store moves from `~/.local/share/guppi/tracker` to a git repo at
  `~/src/github.com/samdengler/tracker`, so it can be connected to Cowork as
  a folder and committed.
- Each machine has its own store. No shared remote is required.
- The bd release is pinned in two places that must agree: `BD_VERSION` in
  the Makefile and the `github:gastownhall/beads` entry in
  `~/.dotfiles/mise/config.toml`.
- The Linux binary for the Cowork VM is downloaded by the Mac and stored
  gitignored in `<store>/bin/`. The VM never needs network access.
- One writer at a time. Dolt runs embedded; concurrent writers over the FUSE
  mount are untested and assumed unsafe.

## Verified on 2026-09-12 (personal Mac)

- bd 1.2.2 linux/arm64 runs inside the Cowork VM and initializes a store on a
  connected folder.
- A four-task diamond (A blocks B and C; B and C block D) resolved correctly
  with closes alternating between the VM and the Mac.
- Binaries execute from the FUSE mount.

## Not yet verified

- The same flow on the work Mac (github.com blocked in its VM, reachable
  from the Mac itself).
- Dolt behavior if two writers do collide.

## Tags and the Alfred workflow

The old tag conventions (toread, idea, followup, and so on) map onto bd
labels (`-l`). The Alfred quick-capture workflow depended on `guppi-tracker
add` and was removed with it; a replacement would call `bin/bd create`.
