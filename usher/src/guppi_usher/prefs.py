"""User preferences for usher — format and seat preferences per theater.

Stored as JSON under the XDG data dir so it is portable user data:
    ~/.local/share/guppi/usher/preferences.json

Seeded on first use with the owner's known Regal/AMC preferences. Anchor seat
preferences on the chain's own "Screen N" label (the user's hand-numbering of
auditoriums was approximate).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

APP = "usher"


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "guppi" / APP


def prefs_path() -> Path:
    return data_dir() / "preferences.json"


# Seed reflects preferences gathered 2026-05-30. Screen labels marked "TBD" are
# to be confirmed from the seat-map header the next time that room is opened.
_SEED = {
    "format_preferences": {
        "regal": ["IMAX", "RPX", "Standard"],
        "amc": ["Dolby"],
        "skip": ["ScreenX"],
        "action_only": ["4DX"],
    },
    "theatres": {
        "regal-atlantic-station": {
            "chain": "regal",
            "theatre_code": "1346",
            "screens": {
                "Screen 11": {"format": "IMAX", "picks": ["K15", "K16", "J15", "J16", "J12", "J13", "I13", "I14"]},
                "Screen 9": {"format": "Standard", "picks": ["L8"]},
                "ScreenX": {"format": "ScreenX", "picks": ["G7", "G8"], "screen_tbd": True},
                "Theatre 17 (TBD)": {"format": "Standard", "picks": ["H8", "H9"], "screen_tbd": True}
            }
        },
        "amc-madison-yards": {
            "chain": "amc",
            "auditoriums": {
                "1 (Dolby)": {"format": "Dolby", "picks": ["H9", "H10"]},
                "2": {"picks": ["G7", "G8"]},
                "5": {"picks": ["G5", "G6", "F7"]}
            }
        }
    }
}


def load() -> dict:
    path = prefs_path()
    if not path.exists():
        return json.loads(json.dumps(_SEED))  # deep copy of seed
    return json.loads(path.read_text())


def save(prefs: dict) -> Path:
    path = prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(prefs, indent=2))
    return path


def ensure_seeded() -> Path:
    """Write the seed file if none exists yet. Idempotent."""
    path = prefs_path()
    if not path.exists():
        save(_SEED)
    return path


def format_order(prefs: dict, chain: str) -> list[str]:
    return prefs.get("format_preferences", {}).get(chain.lower(), [])


def picks_for_screen(prefs: dict, theatre_slug: str, screen: str) -> Optional[list[str]]:
    """Return saved seat-id picks for a screen label, if any."""
    theatre = prefs.get("theatres", {}).get(theatre_slug, {})
    screens = theatre.get("screens", {}) or theatre.get("auditoriums", {})
    entry = screens.get(screen)
    return entry.get("picks") if entry else None
