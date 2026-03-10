---
name: futzer
description: >
  Opinionated config generator you own and understand.
  Use when you need to generate, apply, or manage configuration across machines.
allowed-tools: "Bash(guppi-futzer:*)"
version: "0.1.1"
author: "Sam Dengler"
license: "MIT"
---

# Futzer — Opinionated config generator

Generates well-organized, opinionated configuration files you own and understand. Uses profiles so one config.toml works across all your machines.

## Commands

### `guppi-futzer generate zsh`

Generate zsh config and print to stdout.

**Options:**
- `--profile` / `-p` — profile name (default: `$FUTZER_PROFILE` or `default`)
- `--output` / `-o` — write to file instead of stdout

**Examples:**
```bash
guppi-futzer generate zsh                          # Print to stdout
guppi-futzer generate zsh --profile work            # Use work profile
guppi-futzer generate zsh -o ~/dotfiles/zsh.zsh     # Write to file
```

### `guppi-futzer apply`

Generate all configs to `~/.config/guppi/futzer/` and wire into `.zshrc`.

**Options:**
- `--profile` / `-p` — profile name

```bash
guppi-futzer apply                    # Apply with default profile
guppi-futzer apply --profile work     # Apply with work profile
```

### `guppi-futzer status`

Show active profile, generated files, and whether `.zshrc` sources futzer.

```bash
guppi-futzer status
```

## Configuration

Config file: `~/.config/guppi/futzer/config.toml`

```toml
[default]
# Shared base — opinionated defaults are baked in

[home]
terminal = "ghostty"

[work]
terminal = "iterm2"
```

Set `FUTZER_PROFILE` env var for automatic profile selection.

## Skill Management

```bash
guppi-futzer skill install   # Register with guppi-cli
guppi-futzer skill show      # Display SKILL.md contents
```
