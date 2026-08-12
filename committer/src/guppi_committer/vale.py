"""Optional Vale integration.

Runs the Vale prose linter on the commit message when available and maps
its alerts into committer violations. Also writes a starter Vale config:
the Google developer documentation style package plus an STE approximation
generated from the word lists in checks.py, so both stay in sync.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from guppi_committer.checks import FILLER_PHRASES, SUBSTITUTIONS, Violation

SEVERITY_MAP = {"suggestion": "warning", "warning": "warning", "error": "error"}

VALE_INI = """\
StylesPath = styles
MinAlertLevel = suggestion
Packages = Google

[*]
BasedOnStyles = Vale, Google, STE
"""


def find_vale() -> str | None:
    """Return the vale binary path, or None if not installed."""
    return shutil.which("vale")


def config_dir() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "guppi" / "committer" / "vale"


def default_config() -> Path | None:
    """Return the guppi-managed Vale config, or None if not set up."""
    ini = config_dir() / ".vale.ini"
    return ini if ini.exists() else None


def run(text: str, config: Path | None = None) -> list[Violation]:
    """Run vale on the message text and return its alerts as violations.

    Raises RuntimeError if vale fails to run (for example, a bad config).
    """
    cmd = ["vale", "--output=JSON"]
    if config is not None:
        cmd.append(f"--config={config}")
    with tempfile.TemporaryDirectory() as tmp:
        msg = Path(tmp) / "COMMIT_EDITMSG.md"
        msg.write_text(text)
        cmd.append(str(msg))
        proc = subprocess.run(cmd, capture_output=True, text=True)

    # Vale exits 0 with no alerts and 1 with alerts; anything else is a
    # runtime failure.
    if proc.returncode not in (0, 1):
        raise RuntimeError(proc.stderr.strip() or "vale failed")
    if not proc.stdout.strip():
        return []
    try:
        alerts_by_file = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []

    violations = []
    for alerts in alerts_by_file.values():
        for alert in alerts:
            violations.append(Violation(
                line=alert.get("Line", 1),
                rule=f"vale:{alert.get('Check', 'unknown')}",
                severity=SEVERITY_MAP.get(alert.get("Severity"), "warning"),
                message=alert.get("Message", ""),
            ))
    return violations


def write_config() -> Path:
    """Write the starter Vale config and STE style. Idempotent."""
    style_dir = config_dir() / "styles" / "STE"
    style_dir.mkdir(parents=True, exist_ok=True)

    ini = config_dir() / ".vale.ini"
    ini.write_text(VALE_INI)
    (style_dir / "Substitutions.yml").write_text(_substitutions_yaml())
    (style_dir / "Filler.yml").write_text(_filler_yaml())
    return ini


def _substitutions_yaml() -> str:
    lines = [
        "extends: substitution",
        "message: \"Replace '%s' with '%s'.\"",
        "level: warning",
        "ignorecase: true",
        "swap:",
    ]
    for term, replacement in sorted(SUBSTITUTIONS.items()):
        lines.append(f"  {term}: {replacement}")
    return "\n".join(lines) + "\n"


def _filler_yaml() -> str:
    lines = [
        "extends: existence",
        "message: \"Remove filler: '%s'.\"",
        "level: warning",
        "ignorecase: true",
        "tokens:",
    ]
    for phrase in sorted(FILLER_PHRASES):
        lines.append(f"  - {phrase}")
    return "\n".join(lines) + "\n"
