---
name: dotfiles
description: >
  Add, remove, and reconcile machine dependencies through the dotfiles manifests
  (Brewfile and mise config). Use instead of running brew install or mise install
  directly, so every tool on the machine is recorded in ~/.dotfiles.
allowed-tools: "Bash(guppi-dotfiles:*)"
version: "0.1.0"
author: "Sam Dengler"
license: "MIT"
---

# Dotfiles — Dependency manager for the dotfiles manifests

The dotfiles repo at `~/.dotfiles` holds two manifests: `Brewfile` for Homebrew formulae and casks, and `mise/config.toml` for developer tools. This skill installs packages through those manifests so the repo stays the source of truth for what is on the machine.

Use `guppi-dotfiles add` whenever a task needs a new CLI tool, runtime, or app. Do not run `brew install` or `mise install` directly.

Routing prefers mise. A package goes to Homebrew only when mise cannot install it, and to a cask when Homebrew knows it only as a cask. Pass `--via` to override.

## Commands

### `guppi-dotfiles add <package>... [--via mise|brew|cask]`

Install packages and record them in the matching manifest. mise specs may carry a version (`node@24`) or a backend prefix (`npm:netlify-cli`, `pipx:httpie`).

```bash
guppi-dotfiles add jq                    # mise registry has it, so mise
guppi-dotfiles add node@24               # pinned mise version
guppi-dotfiles add npm:aws-cdk           # backend prefix, always mise
guppi-dotfiles add colima                # not in mise, falls back to brew
guppi-dotfiles add ghostty               # brew knows it as a cask
guppi-dotfiles add bat --via brew        # force Homebrew
```

After adding, commit the manifest change in `~/.dotfiles`.

### `guppi-dotfiles remove <package>... [--keep]`

Remove packages from the manifest they live in and uninstall them. `--keep` edits the manifest only.

```bash
guppi-dotfiles remove jq
guppi-dotfiles remove docker-compose --keep
```

### `guppi-dotfiles list [--json]`

List every package in the manifests with the backend that owns it.

### `guppi-dotfiles drift [--json] [--fix] [--dry-run] [--via ...]`

Compare installed packages against the manifests. Reports packages installed outside the manifests (extra) and manifest entries not installed here (missing).

`--fix` re-adds each extra through normal routing and runs `sync` for missing entries. A brew formula that mise can install is recorded under mise; the brew copy is left installed and reported so it can be uninstalled by hand. Use `--dry-run` to see the plan first.

```bash
guppi-dotfiles drift
guppi-dotfiles drift --json
guppi-dotfiles drift --fix --dry-run
guppi-dotfiles drift --fix
guppi-dotfiles drift --fix --via brew    # keep everything in Homebrew
```

### `guppi-dotfiles sync`

Install every manifest entry that is missing on this machine. Does not upgrade. Use after pulling `~/.dotfiles` on another machine.

### `guppi-dotfiles ignore [<name>...] [--remove] [--json]`

Packages that drift should stop reporting. With no names, print the list.

```bash
guppi-dotfiles ignore cmake poppler
guppi-dotfiles ignore --remove cmake
guppi-dotfiles ignore
```

## Configuration

- `DOTFILES_PATH` sets the dotfiles repo (default `~/.dotfiles`). The Brewfile is read from `$DOTFILES_PATH/Brewfile`.
- mise's global config is read from `MISE_GLOBAL_CONFIG_FILE` or `~/.config/mise/config.toml`, which the dotfiles bootstrap symlinks into the repo.
- The ignore list lives in `~/.config/guppi/dotfiles/config.json`.

## Skill Management

```bash
guppi-dotfiles skill install   # Register with guppi-cli
guppi-dotfiles skill show      # Display SKILL.md contents
```
