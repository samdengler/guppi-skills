---
name: tracker
description: >
  Work item tracker built on Beads (bd). Use it to add work items, break them
  into dependent tasks, find what is ready to work on, claim and close tasks,
  and record follow-ups. Works from Claude Code on the Mac and from Claude
  Cowork sessions through the connected tracker folder.
allowed-tools: "Bash(bin/bd:*),Bash(bd:*),Bash($HOME/mnt/tracker/bin/bd:*)"
version: "1.0.0"
author: "Sam Dengler"
license: "MIT"
---

# Tracker: work items with dependencies, on Beads

The store is a directory with a `.beads/` database and a `bin/bd` shim. Run
every command through the shim; it picks the host's binary and pins the store,
so the working directory does not matter.

| Where the session runs | Command prefix |
|---|---|
| Claude Code or terminal on the Mac | `~/src/github.com/samdengler/tracker/bin/bd` |
| Claude Cowork (device_bash in the VM) | `$HOME/mnt/tracker/bin/bd` |

Set `BD` to the prefix once per session and use `$BD` below.

## Model

A work item is an issue. A work item with dependent tasks is an epic with
child issues. Ordering is expressed only with `blocks` edges: tasks that may
run in parallel are siblings with no edge between them; tasks that must run in
sequence form a chain. `$BD ready` returns every open task whose blockers are
closed, which is the set that can be worked on now, in parallel.

## Commands

### See what is ready

```bash
$BD ready                       # open, unblocked tasks
$BD ready --explain             # same, with the reason each task is ready or blocked
$BD list                        # all open issues
$BD show <id>                   # one issue with its dependencies and comments
```

### Add work

```bash
$BD create "Standalone item" -p 2
$BD create "Bigger work item" -t epic -p 1
$BD create "First task"  -p 1 --parent <epic-id>
$BD create "Second task" -p 1 --parent <epic-id>
```

Priority is 0 (highest) to 4. Add `-d "..."` for a description and
`-l label` for labels.

### Express order

```bash
$BD dep add <task> <blocker>          # task cannot start until blocker closes
$BD dep add <task> --blocked-by <b>   # same, explicit form
```

Leave sibling tasks without edges when they can run in parallel.

### Work a task

```bash
$BD update <id> --claim               # sets in_progress and assignee
$BD comment <id> "what happened"      # progress note
$BD close <id> -r "what was done"     # close with a reason
$BD close <id> -r "..." --suggest-next   # also print what this unblocked
```

### Record a follow-up discovered while working

```bash
$BD create "Follow-up title" -p 2 --deps discovered-from:<current-id>
```

### Machine-readable output

Every listing command accepts `--json`.

## Session close

Run this before ending any session that changed the store:

```bash
STORE=$(dirname "$(dirname "$BD")")
$BD export -o issues.jsonl
git -C "$STORE" add -A && git -C "$STORE" commit -q -m "tracker: session $(date +%F)" || true
```

`issues.jsonl` is the readable, committed copy of the data; the Dolt files
under `.beads/` are the source of truth and are gitignored.

## Rules

- One writer at a time. Do not run bd from the Mac and a Cowork session at
  the same moment.
- Do not use TodoWrite, TaskCreate, or markdown checklists for work that
  belongs in the tracker.
- The bd version is pinned (see `BD_VERSION` in the Makefile and
  `~/.dotfiles/mise/config.toml`). Do not upgrade it inside a work session.

## Setup (once per machine)

```bash
cd ~/src/github.com/samdengler/guppi-skills/tracker
make init            # creates the store, downloads the VM binary, installs the shim
make install-skill   # links this SKILL.md into ~/.claude/skills/tracker
make test            # round-trip test on a throwaway store
```

Then connect `~/src/github.com/samdengler/tracker` as a folder in Claude
Cowork. See README.md for details.
