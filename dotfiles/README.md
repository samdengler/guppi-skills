# guppi-dotfiles

Add, remove, and reconcile machine dependencies through the dotfiles manifests (`~/.dotfiles/Brewfile` and `~/.dotfiles/mise/config.toml`).

The dotfiles repo is meant to rebuild a Mac from scratch. That only works if every tool installed by hand also lands in a manifest. This skill wraps `brew bundle add` and `mise use --global` so an install and its manifest entry happen together, and it reports drift when they did not.

## Install

```bash
guppi skills install dotfiles --source guppi-skills
# or
cd dotfiles && uv tool install .
```

## Usage

```bash
guppi-dotfiles add jq                 # routes to mise when mise can install it
guppi-dotfiles add colima             # falls back to Homebrew
guppi-dotfiles add ghostty            # cask
guppi-dotfiles remove jq
guppi-dotfiles list
guppi-dotfiles drift                  # installed vs. manifests
guppi-dotfiles drift --fix --dry-run  # plan for adopting strays
guppi-dotfiles sync                   # install missing manifest entries
guppi-dotfiles ignore cmake           # stop reporting a package
```

See [SKILL.md](SKILL.md) for the full command reference.

## Development

```bash
uv sync
uv run guppi-dotfiles --help
uv run pytest
```
