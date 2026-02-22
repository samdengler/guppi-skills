"""XDG Base Directory helpers for snapper."""

import os
from pathlib import Path

APP_NAME = "guppi"
SKILL_NAME = "snapper"


def config_dir() -> Path:
    """Config directory: $XDG_CONFIG_HOME/guppi/snapper or ~/.config/guppi/snapper"""
    base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(base) / APP_NAME / SKILL_NAME


def data_dir() -> Path:
    """Data directory: $XDG_DATA_HOME/guppi/snapper or ~/.local/share/guppi/snapper"""
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / APP_NAME / SKILL_NAME


def profiles_dir() -> Path:
    """Profiles directory: data_dir()/profiles"""
    return data_dir() / "profiles"


def extensions_dir() -> Path:
    """Extensions directory: data_dir()/extensions"""
    return data_dir() / "extensions"


def profile_path(name: str) -> Path:
    """Path to a specific named profile."""
    return profiles_dir() / name


def state_file() -> Path:
    """Path to the chromium state file (chromium.json)."""
    return data_dir() / "chromium.json"


def config_file() -> Path:
    """Path to the config file (config.toml)."""
    return config_dir() / "config.toml"
