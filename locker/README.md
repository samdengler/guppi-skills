# Locker

Deterministic secret storage for guppi skills.

**Status:** Active | **Version:** 0.1.0 | **Created:** 2026-03-09

## What it does

Locker gives guppi skills a single place to store and retrieve secrets. Instead of scattering API tokens across env vars, dotfiles, and config directories, locker encrypts them all into one file (`~/.local/share/guppi/locker/secrets.enc`) using a master key stored in the OS keychain. Skills call `guppi-locker get SERVICE KEY` and get back the value — no env vars to remember, no config files to manage.

Secrets are organized by service and key (e.g., `courier/handoffs`, `snapper/api-token`), so each skill's secrets stay namespaced and discoverable.

## When to use it

- Storing an API token or secret that a guppi skill needs
- Retrieving secrets in scripts or other skills without hardcoding values
- Auditing which secrets are stored across your guppi setup
- Centralizing secrets that were previously scattered across env vars

## Quick start

```bash
# First-time setup (once per machine)
guppi-locker init

# Store a secret
guppi-locker set courier handoffs --value "your-token-here"

# Store a secret interactively (prompts for value, hidden input)
guppi-locker set snapper api-token

# Retrieve a secret
guppi-locker get courier handoffs

# Use in scripts
TOKEN=$(guppi-locker get courier handoffs)

# See what's stored
guppi-locker list
```

## What to expect

When you run `guppi-locker init`, it:

1. Generates a Fernet encryption master key
2. Stores the master key in the macOS Keychain
3. Creates an empty encrypted secrets file at `~/.local/share/guppi/locker/secrets.enc`
4. Prints the secrets file path for confirmation

After that, `set` and `get` encrypt/decrypt transparently. Values never touch disk in plaintext. The `list` command shows service/key pairs but never prints secret values.

## Commands

### `guppi-locker init`

First-time setup. Generates a master key, stores it in the OS keychain, and creates the encrypted secrets file. Idempotent — safe to run if already initialized.

- `--force` — regenerate master key and destroy all existing secrets

### `guppi-locker set SERVICE KEY`

Store a secret. Prompts interactively for the value (hidden input) unless `--value` is provided.

- `--value` — provide the secret value inline (useful for scripts)
- `--force` — overwrite an existing secret without confirmation

```bash
guppi-locker set courier handoffs --value "token-value"
guppi-locker set courier handoffs               # prompts for value
guppi-locker set courier handoffs --force        # overwrite without asking
```

### `guppi-locker get SERVICE KEY`

Retrieve a secret. Prints the raw value to stdout with no trailing newline, making it safe for shell substitution.

```bash
TOKEN=$(guppi-locker get courier handoffs)
```

### `guppi-locker delete SERVICE KEY`

Remove a secret permanently. Exits with an error if the secret does not exist.

### `guppi-locker list [SERVICE]`

List all stored secrets by service and key. Never prints secret values.

- Without arguments — shows a table of all services and keys
- With a service name — shows only keys for that service

```bash
guppi-locker list              # all secrets
guppi-locker list courier      # just courier's secrets
```

## Configuration

Locker uses XDG conventions and the macOS Keychain. There are no environment variables to configure.

| Path | Purpose |
|------|---------|
| `~/.local/share/guppi/locker/secrets.enc` | Encrypted secrets file |
| macOS Keychain (`guppi/locker`) | Master encryption key |

## Prerequisites

- Python 3.11+
- macOS (uses the macOS Keychain for master key storage)
- [guppi-cli](https://github.com/agent-skills/guppi-cli) (for `guppi skills install`)
