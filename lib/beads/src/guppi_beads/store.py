"""BeadsStore — wraps the bd CLI for use by guppi skills."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


class BeadsStore:
    """Wraps a per-skill beads instance at ~/.local/share/guppi/<skill_name>/."""

    def __init__(self, skill_name: str, prefix: str | None = None) -> None:
        self._skill_name = skill_name
        self._prefix = prefix

    # -- Properties ----------------------------------------------------------

    @property
    def data_dir(self) -> Path:
        """XDG data directory for this skill."""
        return Path.home() / ".local" / "share" / "guppi" / self._skill_name

    @property
    def initialized(self) -> bool:
        """Whether beads has been initialized (database exists)."""
        return (self.data_dir / ".beads" / "beads.db").exists()

    # -- Core methods --------------------------------------------------------

    def available(self) -> bool:
        """Check if the ``bd`` CLI is on PATH."""
        return shutil.which("bd") is not None

    def ensure(self) -> bool:
        """Initialize beads if needed. Returns True if beads is usable."""
        if not self.available():
            return False

        if self.initialized:
            return True

        self.data_dir.mkdir(parents=True, exist_ok=True)

        args = ["init", "--skip-hooks", "--skip-merge-driver"]
        if self._prefix:
            args.extend(["--prefix", self._prefix])

        result = self.run(args)
        return result.returncode == 0

    def run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        """Run a ``bd`` command with cwd set to the skill's data directory."""
        if not self.available():
            return subprocess.CompletedProcess(
                args=["bd", *args],
                returncode=1,
                stdout="",
                stderr="bd: command not found",
            )

        return subprocess.run(
            ["bd", *args],
            cwd=self.data_dir,
            capture_output=True,
            text=True,
        )

    # -- Query helpers -------------------------------------------------------

    def find_by_title(self, title: str) -> dict | None:
        """Find a single issue by exact title match."""
        issues = self.list_issues(all=True)
        for issue in issues:
            if issue.get("title") == title:
                return issue
        return None

    def list_issues(
        self, status: str | None = None, all: bool = False
    ) -> list[dict]:
        """List issues as dicts. Optional status filter or all=True for closed."""
        args = ["list", "--json"]
        if all:
            args.append("--all")
        if status:
            args.extend(["--status", status])

        result = self.run(args)
        if result.returncode != 0:
            return []

        try:
            return json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            return []
