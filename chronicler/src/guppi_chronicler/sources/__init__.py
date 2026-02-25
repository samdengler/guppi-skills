"""Source adapter registry."""

from .base import HistoryEntry, SourceAdapter
from .chrome import ChromeAdapter
from .terminal import TerminalAdapter

ADAPTER_TYPES: dict[str, type[SourceAdapter]] = {
    "chrome": ChromeAdapter,
    "terminal": TerminalAdapter,
}


def get_adapter(name: str, source_type: str, path: str | None = None) -> SourceAdapter:
    """Create an adapter instance for the given source type."""
    cls = ADAPTER_TYPES.get(source_type)
    if cls is None:
        raise ValueError(f"Unknown source type: '{source_type}'. Known types: {', '.join(ADAPTER_TYPES)}")
    return cls(name=name, path=path)


__all__ = [
    "ADAPTER_TYPES",
    "ChromeAdapter",
    "HistoryEntry",
    "SourceAdapter",
    "TerminalAdapter",
    "get_adapter",
]
