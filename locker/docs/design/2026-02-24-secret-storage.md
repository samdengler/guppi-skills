# Locker — deterministic secret storage for guppi skills

## Problem

Guppi skills need API tokens and other secrets (Telegram bot tokens, API keys, etc.). Currently these live in `~/.zshrc` as env vars — plaintext, visible in `env` output, easy to leak in logs.

Every skill inventing its own way to find secrets leads to inconsistency. Locker provides one deterministic interface so any skill can store and retrieve secrets the same way.

## Solution

A master encryption key is stored in the OS keychain. All secrets are encrypted locally in a single file. No external service dependencies, no cloud sync, no backend abstraction — one implementation that works everywhere.

## Design

### Architecture

```
OS Keychain (macOS security / Linux secret-tool)
    └── one master key: guppi/locker → master-key
            │
            ▼
~/.config/guppi/locker/secrets.enc   (Fernet-encrypted JSON)
    ├── courier/handoffs = "token-value"
    ├── courier/openclaw = "other-value"
    └── snapper/api-key  = "abc123"
```

- **Master key**: A single Fernet key stored in the OS keychain via `security` CLI (macOS). Only one keychain interaction per operation.
- **Secrets file**: Fernet-encrypted JSON blob at `~/.config/guppi/locker/secrets.enc`. All secrets in one file, decrypted in memory, never written to disk in plaintext.
- **Fernet**: AES-128-CBC + HMAC-SHA256 via the `cryptography` library. Authenticated encryption — tamper-evident.

### Keychain entry

| Field | Value |
|-------|-------|
| service (`-s`) | `guppi/locker` |
| account (`-a`) | `master-key` |
| password (`-w`) | Fernet key (base64, 44 chars) |

### Encrypted file format

The plaintext (before encryption) is JSON:

```json
{
  "courier": {
    "handoffs": "token-value",
    "openclaw": "other-value"
  },
  "snapper": {
    "api-key": "abc123"
  }
}
```

Nested by service for clean listing. Encrypted with Fernet, written as a single blob to `secrets.enc`.

### Naming conventions

- **Service** = the skill name without the `guppi-` prefix (e.g., `courier`, not `guppi-courier`)
- **Key** = the specific secret name (e.g., `handoffs`, `api-key`)

## Commands

### `guppi-locker init`

One-time setup. Generates a Fernet master key, stores it in the OS keychain, creates an empty encrypted secrets file.

```bash
$ guppi-locker init
Generating master key... done.
Storing in keychain... done.
Created ~/.config/guppi/locker/secrets.enc
```

Re-running `init` is a no-op if already initialized. Use `--force` to regenerate (destroys all existing secrets).

### `guppi-locker set SERVICE KEY [--value VALUE] [--force]`

Store a secret. If `--value` is omitted, prompt interactively (hides input).

```bash
guppi-locker set courier handoffs --value "123456:ABC-DEF..."
guppi-locker set courier handoffs  # prompts for value
```

If the key already exists, asks for confirmation:

```bash
$ guppi-locker set courier handoffs --value "new-token"
Secret 'courier/handoffs' already exists. Overwrite? [y/N]:
```

Use `--force` to skip the confirmation.

### `guppi-locker get SERVICE KEY`

Retrieve a secret. Prints the value to stdout (for piping/subshell use by other skills).

```bash
token=$(guppi-locker get courier handoffs)
```

Exits non-zero if the key doesn't exist. Errors go to stderr so stdout is clean for piping.

### `guppi-locker delete SERVICE KEY`

Remove a secret.

### `guppi-locker list [SERVICE]`

List keys. Without a service, lists all services and their keys. With a service, lists keys for that service. Never prints secret values.

```bash
$ guppi-locker list
  Service     Key
  courier     handoffs
  courier     openclaw

$ guppi-locker list courier
  handoffs
  openclaw
```

## How other skills use locker

Skills call locker as a subprocess — no Python import dependency, just a CLI contract.

```python
import subprocess

def get_secret(service: str, key: str) -> str:
    result = subprocess.run(
        ["guppi-locker", "get", service, key],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Secret not found: {service}/{key}")
    return result.stdout.strip()

# Usage in courier:
token = get_secret("courier", "handoffs")
```

No shared library, no import coupling. Any tool that can call a subprocess can use locker.

## Dependencies

- **typer** — CLI framework (standard guppi dependency)
- **cryptography** — Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256)
- **macOS `security` CLI** — stores the single master key in the OS keychain
