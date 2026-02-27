"""Profile-based configuration for futzer."""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "guppi" / "futzer"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG = """\
[default]
# Shared base — opinionated defaults are baked into code.
# Override per-machine settings in named profiles below.

# [home]
# terminal = "ghostty"

# [work]
# terminal = "iterm2"
"""


@dataclass
class Profile:
    """Resolved configuration for a single profile."""
    name: str
    terminal: str = "ghostty"


def resolve_profile_name(profile: str | None = None) -> str:
    """Determine the active profile name.

    Priority: explicit arg > $FUTZER_PROFILE > "default"
    """
    if profile:
        return profile
    return os.environ.get("FUTZER_PROFILE", "default")


def load_config(config_path: Path | None = None) -> dict:
    """Load and parse config.toml. Returns empty dict if file doesn't exist."""
    path = config_path or CONFIG_FILE
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text())


def resolve_profile(
    profile_name: str | None = None,
    config_path: Path | None = None,
) -> Profile:
    """Load config and resolve a profile with inheritance from [default].

    Args:
        profile_name: Profile to resolve (None uses env/default).
        config_path: Override config file location.
    """
    name = resolve_profile_name(profile_name)
    config = load_config(config_path)

    # Start with defaults baked into the dataclass
    merged = {}

    # Layer on [default] section from config
    if "default" in config:
        merged.update(config["default"])

    # Layer on named profile (if not "default" itself)
    if name != "default" and name in config:
        merged.update(config[name])

    return Profile(
        name=name,
        terminal=merged.get("terminal", "ghostty"),
    )


def ensure_config(config_path: Path | None = None) -> Path:
    """Create config.toml with defaults if it doesn't exist. Returns the path."""
    path = config_path or CONFIG_FILE
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG)
    return path
