"""Encrypted secret storage backed by OS keychain for the master key."""

import json
import subprocess
import sys
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


KEYCHAIN_SERVICE = "guppi/locker"
KEYCHAIN_ACCOUNT = "master-key"
DATA_DIR = Path.home() / ".local" / "share" / "guppi" / "locker"
SECRETS_FILE = DATA_DIR / "secrets.enc"


class SecretExistsError(Exception):
    def __init__(self, service: str, key: str):
        self.service = service
        self.key = key
        super().__init__(f"Secret '{service}/{key}' already exists.")


class SecretNotFoundError(Exception):
    def __init__(self, service: str, key: str):
        self.service = service
        self.key = key
        super().__init__(f"Secret '{service}/{key}' not found.")


# --- Keychain operations (master key only) ---


def _store_master_key(key: bytes) -> None:
    """Store the Fernet master key in the OS keychain."""
    if sys.platform != "darwin":
        raise RuntimeError("Only macOS is currently supported.")
    result = subprocess.run(
        ["security", "add-generic-password", "-U",
         "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT,
         "-w", key.decode()],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to store master key: {result.stderr.strip()}")


def _get_master_key() -> bytes:
    """Retrieve the Fernet master key from the OS keychain."""
    if sys.platform != "darwin":
        raise RuntimeError("Only macOS is currently supported.")
    result = subprocess.run(
        ["security", "find-generic-password",
         "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT, "-w"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "Master key not found in keychain.\n"
            "Run 'guppi-locker init' to set up locker."
        )
    return result.stdout.strip().encode()


def _delete_master_key() -> None:
    """Remove the master key from the OS keychain."""
    subprocess.run(
        ["security", "delete-generic-password",
         "-s", KEYCHAIN_SERVICE, "-a", KEYCHAIN_ACCOUNT],
        capture_output=True, text=True,
    )


# --- Encrypted file operations ---


def _read_secrets() -> dict[str, dict[str, str]]:
    """Decrypt and read the secrets file. Returns empty dict if no file."""
    if not SECRETS_FILE.exists():
        return {}
    key = _get_master_key()
    f = Fernet(key)
    try:
        plaintext = f.decrypt(SECRETS_FILE.read_bytes())
    except InvalidToken:
        raise RuntimeError(
            "Failed to decrypt secrets file. Master key may have changed.\n"
            "If you re-initialized, the old secrets are unrecoverable."
        )
    return json.loads(plaintext)


def _write_secrets(secrets: dict[str, dict[str, str]]) -> None:
    """Encrypt and write the secrets file."""
    key = _get_master_key()
    f = Fernet(key)
    plaintext = json.dumps(secrets, indent=2).encode()
    SECRETS_FILE.write_bytes(f.encrypt(plaintext))


# --- Public API ---


def is_initialized() -> bool:
    """Check if locker has been initialized."""
    return SECRETS_FILE.exists()


def initialize(force: bool = False) -> None:
    """Generate master key, store in keychain, create empty secrets file."""
    if is_initialized() and not force:
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Generate and store master key
    master_key = Fernet.generate_key()
    _store_master_key(master_key)

    # Create empty encrypted secrets file
    f = Fernet(master_key)
    plaintext = json.dumps({}).encode()
    SECRETS_FILE.write_bytes(f.encrypt(plaintext))


def get(service: str, key: str) -> str:
    """Retrieve a secret value."""
    secrets = _read_secrets()
    svc_secrets = secrets.get(service, {})
    if key not in svc_secrets:
        raise SecretNotFoundError(service, key)
    return svc_secrets[key]


def exists(service: str, key: str) -> bool:
    """Check if a secret exists."""
    secrets = _read_secrets()
    return key in secrets.get(service, {})


def set(service: str, key: str, value: str) -> None:
    """Store a new secret. Raises SecretExistsError if it already exists."""
    secrets = _read_secrets()
    if service in secrets and key in secrets[service]:
        raise SecretExistsError(service, key)
    if service not in secrets:
        secrets[service] = {}
    secrets[service][key] = value
    _write_secrets(secrets)


def update(service: str, key: str, value: str) -> None:
    """Update an existing secret (or create it)."""
    secrets = _read_secrets()
    if service not in secrets:
        secrets[service] = {}
    secrets[service][key] = value
    _write_secrets(secrets)


def delete(service: str, key: str) -> None:
    """Delete a secret."""
    secrets = _read_secrets()
    if service not in secrets or key not in secrets[service]:
        raise SecretNotFoundError(service, key)
    del secrets[service][key]
    if not secrets[service]:
        del secrets[service]
    _write_secrets(secrets)


def list_secrets(service: str | None = None) -> list[tuple[str, str]]:
    """List secrets as (service, key) tuples. Never returns values."""
    secrets = _read_secrets()
    result = []
    for svc, keys in sorted(secrets.items()):
        if service and svc != service:
            continue
        for key in sorted(keys):
            result.append((svc, key))
    return result
