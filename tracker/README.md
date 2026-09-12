# Tracker

Work item tracker built on Beads, usable from Claude Code and Claude Cowork.

**Status:** Active | **Version:** 1.0.0 | **Created:** 2026-03-08 | **Updated:** 2026-09-12

## What it does

Tracker is a Beads (`bd`) store for work items. A work item can stand alone
or be an epic with dependent tasks. Tasks that must run in order are linked
with `blocks` edges; tasks with no edge between them can run in parallel.
`bd ready` returns whatever is unblocked right now, which is what an agent
should pick up next.

Version 1.0 replaced the earlier Python wrapper (`guppi-tracker`) with a
Makefile, a shim, and a SKILL.md that call `bd` directly. The wrapper hid
dependencies, which are the point, and could not run inside a Cowork session.

## Why it works from Cowork

A Cowork session runs its shell in a Linux VM on the Mac. The VM sees only
folders that have been connected to the session, and it has no `bd`. So the
store lives in a folder that gets connected, and a Linux build of `bd` sits
inside that folder next to a shim that picks the right binary for the host.
Both binaries are the same pinned release. Dolt runs embedded (no server), and
writes from either side land in the same files.

The Mac must be able to reach github.com to download the Linux binary once;
the VM never needs to.

## Setup

```bash
# 1. bd on the Mac, pinned, via mise (already in ~/.dotfiles/mise/config.toml)
~/.dotfiles/bootstrap.sh
bd version                      # must match BD_VERSION in the Makefile

# 2. Create the store, fetch the VM binary, install the shim
cd ~/src/github.com/samdengler/guppi-skills/tracker
make init

# 3. Make the skill visible to Claude Code
make install-skill

# 4. Prove it
make test
```

Then, in the Claude desktop app, connect `~/src/github.com/samdengler/tracker`
as a folder for any Cowork session that should use the tracker.

The store is its own git repo. Each machine has its own store; they do not
need to share one. `issues.jsonl` is committed as the readable copy of the
data; the Dolt files are gitignored.

## Daily use

From a terminal or Claude Code:

```bash
cd ~/src/github.com/samdengler/tracker
bin/bd ready
bin/bd create "Write the Gateway design note" -p 1
bin/bd close trk-abc -r "sent for review"
```

From a Cowork session the same commands work with
`$HOME/mnt/tracker/bin/bd`. The SKILL.md carries the full vocabulary.

Close every session that changed the store with `bin/bd export -o issues.jsonl`
and a commit. Only one shell writes to the store at a time.

## Makefile targets

| Target | What it does |
|---|---|
| `init` | Create the store (git init, `bd init`), download the VM binary, install the shim and AGENTS.md |
| `vm-binary` | Download and checksum-verify the Linux `bd` into `<store>/bin/` |
| `shim` | Reinstall `bin/bd` into the store |
| `export` | Write `issues.jsonl` |
| `test` | Round-trip test on a throwaway store |
| `install-skill` | Symlink this directory into `~/.claude/skills/tracker` |

Variables: `BD_VERSION`, `STORE`, `PREFIX`, `VM_ARCH` (arm64 default; use
`amd64` for an Intel Mac).

## Design notes

`docs/design/` holds the history. The current design is
`2026-09-12-beads-for-cowork.md`; the earlier notes describe the retired
Python wrapper.
