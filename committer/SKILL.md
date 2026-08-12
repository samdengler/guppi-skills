---
name: committer
description: >
  Standardize git commit messages. Use whenever you write a commit message:
  draft the message with the rules in this document, then validate it with
  guppi-committer check before committing.
allowed-tools: "Bash(guppi-committer:*)"
version: "0.1.0"
author: "Sam Dengler"
license: "MIT"
---

# Committer: standardized commit messages

Write commit messages that follow a fixed format (Tim Pope 50/72) and plain
technical prose (Simplified Technical English and the Google developer
documentation style guide). Draft the message with the rules below, then run
`guppi-committer check` on the draft. Fix every error and warning it reports
before committing.

## Message format rules

1. Subject line: 50 characters or fewer, capitalized, no trailing period.
2. Subject uses the imperative mood. It must complete the sentence
   "If applied, this commit will ___". Write "Add retry logic", never
   "Added retry logic" or "Adds retry logic".
3. One blank line between the subject and the body.
4. Body lines wrap at 72 characters. Lines with URLs, indented code, and
   trailers (such as `Fixes: #12`) are exempt.
5. The body explains what changed and why. The diff already shows how.
6. Small self-explanatory changes need no body.

## Prose rules for the body

1. Write short sentences: 25 words or fewer, one instruction or fact per
   sentence.
2. Use active voice and present tense: "The parser rejects empty input",
   never "empty input is now rejected by the parser".
3. Use one word per meaning. Pick "delete" or "remove" and use it
   consistently within the message.
4. Remove filler: "simply", "just", "basically", "note that", "of course".
5. Prefer plain words: "use" over "utilize" or "leverage", "to" over
   "in order to", "before" over "prior to", "about" over "approximately".

## Workflow

1. Draft the commit message following the rules above.
2. Validate it before committing:

   ```bash
   printf '%s\n' "<message>" | guppi-committer check --strict
   ```

   Or write the draft to a file and run `guppi-committer check <file>`.
3. If it reports violations, revise the draft and check again. Repeat until
   it prints "Commit message OK".
4. Commit. If the repository has the hook installed, `git commit` runs the
   same check automatically and rejects messages with errors.

## Commands

### `guppi-committer check [file]`

Check a commit message. Reads stdin when no file is given. Exits nonzero on
errors, and prints each violation with a line number, severity, and rule id.

**Options:**
- `--strict` — fail on warnings as well as errors
- `--json` — output violations as JSON
- `--vale` / `--no-vale` — force or skip Vale; the default runs Vale only
  when the binary is installed and `vale-setup` has been run
- `--vale-config` — use a specific Vale config file

### `guppi-committer vale-setup`

Write the Vale config (Google developer documentation style package plus an
STE approximation) and download the packages with `vale sync`. Requires the
`vale` binary. Idempotent. After setup, `check` runs Vale automatically and
reports its alerts as warnings with `vale:` rule prefixes.

**Options:**
- `--no-sync` — write the config without downloading packages

### `guppi-committer init`

Install a `commit-msg` hook in the current repository that runs
`guppi-committer check` on every commit. Idempotent.

**Options:**
- `--force` / `-f` — overwrite a pre-existing hook not owned by committer

## Examples

```bash
git log -1 --format=%B | guppi-committer check          # check the last commit
guppi-committer check .git/COMMIT_EDITMSG               # check a message file
printf 'Add retry logic to fetcher\n' | guppi-committer check --strict
guppi-committer init                                     # enforce via git hook
```

A passing message:

```
Add retry logic to the artifact fetcher

Transient network failures caused nightly builds to fail about once a
week. The fetcher now retries three times with exponential backoff
before it reports an error.

Fixes: #142
```

## Skill Management

```bash
guppi-committer skill install   # Register with guppi-cli
guppi-committer skill show      # Display SKILL.md contents
```
