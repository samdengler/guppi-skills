# committer

Standardizes git commit messages. Checks the format rules from
[Tim Pope's note on commit messages](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html)
and [cbea.ms/git-commit](https://cbea.ms/git-commit/), plus prose rules that
approximate ASD-STE100 (Simplified Technical English) and the
[Google developer documentation style guide](https://developers.google.com/style).

It works two ways: agents read `SKILL.md` and validate their drafts with
`guppi-committer check`, and the `commit-msg` hook rejects nonconforming
messages from any author, human or agent.

## What it checks

Errors (block the commit when the hook is installed):

| Rule | Description |
|------|-------------|
| `subject-length` | Subject over 50 characters |
| `subject-capitalization` | Subject starts lowercase |
| `subject-period` | Subject ends with a period |
| `subject-imperative` | Subject starts with "Added", "Fixes", "Updating", and similar |
| `blank-line-after-subject` | Body not separated from subject by a blank line |
| `body-line-length` | Body line over 72 characters (URLs, code, trailers exempt) |

Warnings (reported, fail only with `--strict`):

| Rule | Description |
|------|-------------|
| `filler-word` | "simply", "just", "basically", "note that", and similar |
| `word-substitution` | "utilize" for "use", "prior to" for "before", and similar |
| `sentence-length` | Sentence over 25 words |

Auto-generated subjects (`Merge`, `Revert`, `fixup!`, `squash!`) are exempt
from subject rules. Comment lines and content after the scissors line are
ignored.

## Setup

```bash
guppi skills install committer     # install and register
cd <your-repo> && guppi-committer init   # optional: enforce via git hook
```

## Vale integration (optional)

With [Vale](https://vale.sh) installed, `check` also lints the message
against the Google developer documentation style package and an STE style
generated from committer's own word lists:

```bash
brew install vale
guppi-committer vale-setup    # writes config, runs vale sync
```

The config lives in `~/.config/guppi/committer/vale/`. After setup, every
`check` (including the git hook) reports Vale alerts as warnings with
`vale:` rule prefixes, for example `vale:Google.Passive`. Use `--no-vale`
to skip it, `--vale` to require it, or `--strict` to make the alerts fatal.

## Usage

```bash
guppi-committer check msg.txt              # check a message file
git log -1 --format=%B | guppi-committer check   # check the last commit
guppi-committer check --strict --json msg.txt    # machine-readable, warnings fatal
```

## Example session

```
$ printf 'added retry logic.\n' | guppi-committer check
line 1: error Capitalize the subject line (subject-capitalization)
line 1: error Use the imperative mood: "Add", not "Added" (subject-imperative)
line 1: error Do not end the subject with a period (subject-period)
Commit message rejected: 3 errors, 0 warnings

$ printf 'Add retry logic to fetcher\n' | guppi-committer check
Commit message OK
```

## CLI reference

| Command | Description |
|---------|-------------|
| `guppi-committer check [file]` | Check a message (stdin if no file); `--strict`, `--json` |
| `guppi-committer init` | Install the commit-msg hook; `--force` to overwrite |
| `guppi-committer skill install` | Register with guppi-cli |
| `guppi-committer skill show` | Display SKILL.md |
