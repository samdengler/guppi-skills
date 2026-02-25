"""Tests for terminal source adapter."""

from datetime import datetime, timezone

import pytest

from guppi_chronicler.sources.terminal import TerminalAdapter


@pytest.fixture
def zsh_history(tmp_path):
    """Create a fake zsh history file."""
    hist = tmp_path / ".zsh_history"
    hist.write_text(
        ": 1740000000:0;git status\n"
        ": 1740000100:0;cd /tmp\n"
        ": 1740000200:0;ls -la\n"
        ": 1740000300:0;git push origin main\n"
    )
    return str(hist)


def test_search_all(zsh_history):
    adapter = TerminalAdapter(name="test", path=zsh_history)
    results = adapter.search()
    assert len(results) == 4
    # Most recent first
    assert "git push" in results[0].summary


def test_search_with_query(zsh_history):
    adapter = TerminalAdapter(name="test", path=zsh_history)
    results = adapter.search(query="git")
    assert len(results) == 2
    assert all("git" in r.summary for r in results)


def test_search_with_since(zsh_history):
    adapter = TerminalAdapter(name="test", path=zsh_history)
    # 1740000200 = 2025-02-19T21:23:20 UTC — after the first 2 entries
    since = datetime(2025, 2, 19, 21, 22, 0, tzinfo=timezone.utc)
    results = adapter.search(since=since)
    assert len(results) == 2


def test_search_with_limit(zsh_history):
    adapter = TerminalAdapter(name="test", path=zsh_history)
    results = adapter.search(limit=2)
    assert len(results) == 2


def test_available(zsh_history):
    adapter = TerminalAdapter(name="test", path=zsh_history)
    assert adapter.available() is True


def test_not_available(tmp_path):
    adapter = TerminalAdapter(name="test", path=str(tmp_path / "nonexistent"))
    assert adapter.available() is False


def test_entry_fields(zsh_history):
    adapter = TerminalAdapter(name="test", path=zsh_history)
    results = adapter.search(query="ls")
    assert len(results) == 1
    entry = results[0]
    assert entry.source == "test"
    assert entry.kind == "command"
    assert entry.summary == "ls -la"
    assert entry.timestamp is not None
