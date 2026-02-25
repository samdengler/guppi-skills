"""Configuration management for chronicler sources."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "guppi" / "chronicler"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    """Load the source registry config."""
    if not CONFIG_FILE.exists():
        return {"sources": {}}
    return json.loads(CONFIG_FILE.read_text())


def save_config(config: dict) -> None:
    """Save the source registry config."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")


def get_sources() -> dict[str, dict]:
    """Return all registered sources."""
    return load_config().get("sources", {})


def get_source(name: str) -> dict | None:
    """Return a single source config by name, or None."""
    return get_sources().get(name)


def add_source(name: str, source_type: str, path: str | None = None) -> None:
    """Register a new source. Raises ValueError if name already exists."""
    config = load_config()
    if name in config.get("sources", {}):
        raise ValueError(f"Source '{name}' already exists")
    config.setdefault("sources", {})[name] = {
        "type": source_type,
        "enabled": True,
        "path": path,
    }
    save_config(config)


def remove_source(name: str) -> None:
    """Unregister a source. Raises ValueError if not found."""
    config = load_config()
    sources = config.get("sources", {})
    if name not in sources:
        raise ValueError(f"Source '{name}' not found")
    del sources[name]
    save_config(config)


def set_source_enabled(name: str, enabled: bool) -> None:
    """Enable or disable a source. Raises ValueError if not found."""
    config = load_config()
    sources = config.get("sources", {})
    if name not in sources:
        raise ValueError(f"Source '{name}' not found")
    sources[name]["enabled"] = enabled
    save_config(config)


def get_enabled_sources() -> dict[str, dict]:
    """Return only enabled sources."""
    return {k: v for k, v in get_sources().items() if v.get("enabled", True)}
