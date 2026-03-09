# Futzer

Opinionated config generator you own and understand.

**Status:** Experimental | **Version:** 0.1.0

## What it does

Futzer generates well-organized, opinionated shell configuration files from a single `config.toml`. Instead of hand-editing dotfiles and copying them between machines, futzer generates config from code with sensible defaults baked in. Profiles let one config file work across all your machines — `home`, `work`, or whatever you need.

Generated files live in `~/.config/guppi/futzer/` and get wired into your `.zshrc` automatically. You own every line of the output — no magic, no hidden state.

## When to use it

- Setting up a new machine and want your shell config in place fast
- Keeping shell config consistent across multiple machines with minor differences
- Wanting opinionated zsh defaults without maintaining a sprawling dotfiles repo
- Switching between terminal emulators on different machines (Ghostty at home, iTerm2 at work)

## Quick start

```bash
# Generate zsh config and preview it
guppi-futzer generate zsh

# Apply everything — generates files and wires into .zshrc
guppi-futzer apply

# Check what's set up
guppi-futzer status
```

## What to expect

When you run `guppi-futzer apply`, it:

1. Creates `~/.config/guppi/futzer/config.toml` if it doesn't exist (with commented examples)
2. Generates `zsh.zsh` with opinionated zsh configuration for your active profile
3. Generates `init.zsh` which sources all enabled modules
4. Adds a source line to your `~/.zshrc` (idempotent — won't duplicate)
5. Prints the active profile and terminal setting

After applying, run `source ~/.config/guppi/futzer/init.zsh` to activate in your current shell. Future shells pick it up automatically.

## Commands

### `guppi-futzer generate zsh`

Generate opinionated zsh config and print to stdout. Useful for previewing before applying, or writing to a custom location.

- `--profile` / `-p` — profile name (default: `$FUTZER_PROFILE` or `default`)
- `--output` / `-o` — write to file instead of stdout

```bash
guppi-futzer generate zsh                          # Preview to stdout
guppi-futzer generate zsh --profile work            # Use work profile
guppi-futzer generate zsh -o ~/dotfiles/zsh.zsh     # Write to specific file
```

### `guppi-futzer apply`

Generate all configs to `~/.config/guppi/futzer/` and wire into `.zshrc`. Creates `config.toml` with defaults if it doesn't exist. Safe to run repeatedly.

- `--profile` / `-p` — profile name (default: `$FUTZER_PROFILE` or `default`)

```bash
guppi-futzer apply                    # Apply with default profile
guppi-futzer apply --profile work     # Apply with work profile
```

### `guppi-futzer status`

Show active profile, generated files, and whether `.zshrc` sources futzer. Quick way to check if everything is wired up.

```bash
guppi-futzer status
```

## Configuration

Config file: `~/.config/guppi/futzer/config.toml`

Profiles inherit from `[default]`. Named profiles override specific values. The active profile is determined by: explicit `--profile` flag, then `$FUTZER_PROFILE` env var, then `default`.

```toml
[default]
# Shared base — opinionated defaults are baked into code.
# Override per-machine settings in named profiles below.

[home]
terminal = "ghostty"

[work]
terminal = "iterm2"
```

### Profile settings

| Setting | Default | Description |
|---------|---------|-------------|
| `terminal` | `ghostty` | Terminal emulator (affects generated config) |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FUTZER_PROFILE` | `default` | Active profile when `--profile` is not passed |

### Generated files

| File | Purpose |
|------|---------|
| `~/.config/guppi/futzer/config.toml` | Profile-based configuration |
| `~/.config/guppi/futzer/init.zsh` | Entry point sourced by `.zshrc` |
| `~/.config/guppi/futzer/zsh.zsh` | Generated zsh configuration |

## Prerequisites

- Python 3.11+
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skill install`)
