"""Config and state management for courier bots."""

import json
import subprocess
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "guppi" / "courier"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_DIR = Path.home() / ".local" / "state" / "guppi" / "courier"
OFFSETS_DIR = STATE_DIR / "offsets"
CHAT_IDS_DIR = STATE_DIR / "chat_ids"


# --- Config (bot registry) ---


def load_config() -> dict:
    """Load the bot registry config. Returns empty structure if missing."""
    if not CONFIG_FILE.exists():
        return {"default": None, "bots": {}}
    return json.loads(CONFIG_FILE.read_text())


def save_config(config: dict) -> None:
    """Write the bot registry config."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")


def get_bot(name: str | None = None) -> tuple[str, dict]:
    """Resolve a bot by name or default. Returns (name, bot_config).

    Raises RuntimeError if no bots are configured or the name is not found.
    """
    config = load_config()
    if not config["bots"]:
        raise RuntimeError("No bots configured. Run: guppi-courier add <name>")
    if name is None:
        name = config.get("default")
        if name is None:
            # Fall back to first bot
            name = next(iter(config["bots"]))
    if name not in config["bots"]:
        available = ", ".join(config["bots"])
        raise RuntimeError(f"Bot '{name}' not found. Available: {available}")
    return name, config["bots"][name]


def add_bot(name: str, bot_name: str | None = None, default: bool = False) -> None:
    """Add a bot to the registry."""
    config = load_config()
    bot_entry: dict = {}
    if bot_name:
        bot_entry["name"] = bot_name
    config["bots"][name] = bot_entry
    if default or config.get("default") is None:
        config["default"] = name
    save_config(config)


def remove_bot(name: str) -> None:
    """Remove a bot from the registry."""
    config = load_config()
    if name not in config["bots"]:
        raise RuntimeError(f"Bot '{name}' not found")
    del config["bots"][name]
    if config.get("default") == name:
        config["default"] = next(iter(config["bots"]), None)
    save_config(config)

    # Clean up state files
    offset_file = OFFSETS_DIR / name
    if offset_file.exists():
        offset_file.unlink()
    chat_id_file = CHAT_IDS_DIR / name
    if chat_id_file.exists():
        chat_id_file.unlink()


# --- Secrets (via guppi-locker) ---


def get_token(name: str) -> str:
    """Retrieve a bot token from locker."""
    result = subprocess.run(
        ["guppi-locker", "get", "courier", name],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Token not found for bot '{name}'. Run: guppi-courier add {name}")
    return result.stdout.strip()


def set_token(name: str, token: str) -> None:
    """Store a bot token in locker."""
    result = subprocess.run(
        ["guppi-locker", "set", "courier", name, "--value", token, "--force"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to store token: {result.stderr.strip()}")


def delete_token(name: str) -> None:
    """Delete a bot token from locker."""
    subprocess.run(
        ["guppi-locker", "delete", "courier", name],
        capture_output=True,
        text=True,
    )


def has_token(name: str) -> bool:
    """Check if a bot has a token in locker."""
    result = subprocess.run(
        ["guppi-locker", "get", "courier", name],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


# --- State (offsets and chat IDs) ---


def get_offset(name: str) -> int | None:
    """Read the stored offset for a bot."""
    path = OFFSETS_DIR / name
    if not path.exists():
        return None
    return int(path.read_text().strip())


def set_offset(name: str, offset: int) -> None:
    """Write the offset for a bot."""
    OFFSETS_DIR.mkdir(parents=True, exist_ok=True)
    (OFFSETS_DIR / name).write_text(str(offset))


def get_chat_id(name: str) -> int | None:
    """Read the stored chat ID for a bot."""
    path = CHAT_IDS_DIR / name
    if not path.exists():
        return None
    return int(path.read_text().strip())


def set_chat_id(name: str, chat_id: int) -> None:
    """Write the chat ID for a bot."""
    CHAT_IDS_DIR.mkdir(parents=True, exist_ok=True)
    (CHAT_IDS_DIR / name).write_text(str(chat_id))
