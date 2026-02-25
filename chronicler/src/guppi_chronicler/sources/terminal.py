"""Terminal/shell history source adapter."""

import os
import re
from datetime import datetime, timezone
from pathlib import Path

from .base import HistoryEntry, SourceAdapter

# zsh extended history format: ": timestamp:duration;command"
ZSH_EXTENDED_RE = re.compile(r"^: (\d+):\d+;(.+)")

# Default history file paths
ZSH_HISTORY = Path.home() / ".zsh_history"
BASH_HISTORY = Path.home() / ".bash_history"


class TerminalAdapter(SourceAdapter):
    """Read shell history (zsh/bash)."""

    def _history_path(self) -> Path:
        """Resolve the history file path."""
        if self.path:
            return Path(self.path)
        # Check HISTFILE env var first
        histfile = os.environ.get("HISTFILE")
        if histfile:
            return Path(histfile)
        # Auto-detect from $SHELL
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell:
            return ZSH_HISTORY
        return BASH_HISTORY

    def _is_zsh(self) -> bool:
        """Determine if we're reading zsh history."""
        path = self._history_path()
        if "zsh" in path.name:
            return True
        shell = os.environ.get("SHELL", "")
        return "zsh" in shell

    def search(
        self,
        query: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
    ) -> list[HistoryEntry]:
        path = self._history_path()
        if not path.exists():
            return []

        # Read raw bytes and decode leniently (history files can have odd encodings)
        raw = path.read_bytes()
        lines = raw.decode("utf-8", errors="replace").splitlines()

        entries: list[HistoryEntry] = []
        is_zsh = self._is_zsh()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            timestamp: datetime | None = None
            command: str

            if is_zsh:
                m = ZSH_EXTENDED_RE.match(line)
                if m:
                    ts_epoch = int(m.group(1))
                    timestamp = datetime.fromtimestamp(ts_epoch, tz=timezone.utc)
                    command = m.group(2)
                else:
                    # Plain zsh line (no timestamp)
                    command = line
            else:
                # bash: check for #epoch timestamp line
                # (timestamps appear as a comment line before the command)
                command = line

            # Filter by time
            if timestamp:
                if since and timestamp < since:
                    continue
                if until and timestamp > until:
                    continue

            # Filter by query
            if query and query.lower() not in command.lower():
                continue

            entries.append(
                HistoryEntry(
                    timestamp=timestamp,
                    source=self.name,
                    kind="command",
                    summary=command,
                )
            )

        # Most recent first, undated at the end
        dated = [e for e in entries if e.timestamp is not None]
        undated = [e for e in entries if e.timestamp is None]
        dated.sort(key=lambda e: e.timestamp, reverse=True)  # type: ignore[arg-type]

        return (dated + undated)[:limit]

    def available(self) -> bool:
        return self._history_path().exists()

    def check_prereqs(self) -> list[str]:
        issues = []
        path = self._history_path()
        if not path.exists():
            issues.append(f"History file not found: {path}")
            return issues

        if self._is_zsh():
            # Check if EXTENDED_HISTORY is set by looking at a sample line
            raw = path.read_bytes()
            sample = raw.decode("utf-8", errors="replace")[:500]
            if not ZSH_EXTENDED_RE.search(sample):
                issues.append(
                    "zsh EXTENDED_HISTORY does not appear to be enabled.\n"
                    "Add the following to ~/.zshrc:\n\n"
                    "    setopt EXTENDED_HISTORY"
                )
        return issues

    def apply_prereqs(self) -> list[str]:
        actions = []
        if self._is_zsh():
            zshrc = Path.home() / ".zshrc"
            content = zshrc.read_text() if zshrc.exists() else ""
            if "EXTENDED_HISTORY" not in content:
                with zshrc.open("a") as f:
                    f.write("\n# Added by guppi-chronicler\nsetopt EXTENDED_HISTORY\n")
                actions.append("Added 'setopt EXTENDED_HISTORY' to ~/.zshrc")
        return actions

    @classmethod
    def detect(cls) -> str | None:
        shell = os.environ.get("SHELL", "")
        if "zsh" in shell and ZSH_HISTORY.exists():
            return str(ZSH_HISTORY)
        if "bash" in shell and BASH_HISTORY.exists():
            return str(BASH_HISTORY)
        # Check common paths regardless of $SHELL
        if ZSH_HISTORY.exists():
            return str(ZSH_HISTORY)
        if BASH_HISTORY.exists():
            return str(BASH_HISTORY)
        return None
