# Tracker store

This directory is a Beads store of work items. It is used from Claude Code on
the Mac and from Claude Cowork sessions (where it is mounted as a connected
folder). Always run Beads through the shim so the right binary and store are
used from any working directory:

    bin/bd <command>            # from this directory
    $HOME/mnt/tracker/bin/bd    # from a Cowork session

The full command vocabulary is in the tracker SKILL.md in guppi-skills.

## Session close

Before ending a session that changed anything:

    bin/bd export -o issues.jsonl
    git add -A && git commit -q -m "tracker: $(date +%F) session" || true

Only one machine or shell writes to this store at a time. Do not run bd from
the Mac and from a Cowork session concurrently.
