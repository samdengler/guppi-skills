# Commit message standardizer

## Motivation

Agent-written commit messages drift in format and tone. The fix has two
layers: instructions that tell the agent what a good message looks like, and
a linter that rejects messages that do not comply. The linter matters more.
Agents follow instructions unreliably but respond well to concrete rejection
feedback: the hook rejects with a specific error, the agent revises and
retries.

Sources for the rules:

- Tim Pope, "A Note About Git Commit Messages" (50/72 format)
- cbea.ms/git-commit (the seven rules)
- ASD-STE100 Simplified Technical English (short sentences, approved words)
- Google developer documentation style guide (active voice, no filler)

## Design

Three parts, matching the two layers plus wiring:

1. `SKILL.md` distills the four sources into explicit drafting rules. Agents
   follow "subject 50 characters or fewer, imperative mood" far better than
   a link to an article.
2. `guppi-committer check` validates a message from a file or stdin. Format
   violations are errors; prose violations are warnings (`--strict` makes
   them fatal). `--json` for machine consumption.
3. `guppi-committer init` installs a `commit-msg` hook so enforcement
   applies to every author and every client.

### Check rules

Format (errors): subject length, capitalization, no trailing period,
imperative first word, blank line after subject, body wrap at 72.

Prose (warnings): filler words, wordy substitutions, sentences over 25
words.

Decisions:

- The imperative check uses an explicit word list, since suffix heuristics
  (-ed, -ing, -s) flag words like "Speed", "Bring", and "Focus".
- Body lines with URLs, indented code, or trailers are exempt from the
  72-character limit. Trailers and code are also exempt from prose rules.
- Auto-generated subjects (`Merge`, `Revert`, `fixup!`, `squash!`) skip
  subject rules.
- Stdlib only, plus the standard Typer and Rich dependencies. No Vale
  dependency: the built-in checks cover commit-sized prose, and requiring a
  separate binary would complicate the hook.

### ASD-STE100 licensing

The STE specification is licensed and has no official open rule package.
The substitution and filler lists here approximate its intent: one word per
meaning, short sentences, plain verbs. Expand the lists over time from real
rejections rather than trying to encode the full spec.

## Future work

- Optional Vale integration: if a `vale` binary and config exist, run it on
  the message body for the full Google style package.
- Conventional Commits mode (`type: subject` prefixes) as an opt-in flag or
  config, layered on the same 50/72 rules.
- Per-repo config for word lists and limits
  (`~/.config/guppi/committer/config.json` or in-repo).
- A `draft` command that takes `git diff --staged` output and prints a
  suggested message for the agent to refine.
