"""Base interface for history source adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HistoryEntry:
    """A single history event from any source."""

    timestamp: datetime | None
    source: str
    kind: str
    summary: str
    detail: str | None = None


class SourceAdapter(ABC):
    """Abstract base for history source adapters."""

    def __init__(self, name: str, path: str | None = None):
        self.name = name
        self.path = path

    @abstractmethod
    def search(
        self,
        query: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 50,
    ) -> list[HistoryEntry]:
        """Search this source for matching history entries."""
        ...

    @abstractmethod
    def available(self) -> bool:
        """Check if this source's backing data is accessible."""
        ...

    @abstractmethod
    def check_prereqs(self) -> list[str]:
        """Check prerequisites. Returns list of issues (empty = ready)."""
        ...

    @abstractmethod
    def apply_prereqs(self) -> list[str]:
        """Fix prerequisites automatically. Returns list of actions taken."""
        ...

    @classmethod
    @abstractmethod
    def detect(cls) -> str | None:
        """Return the default data path if this source exists on the machine, else None."""
        ...
