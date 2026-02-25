"""Tests for Chrome source adapter."""

import sqlite3
from datetime import datetime, timezone

import pytest

from guppi_chronicler.sources.chrome import (
    ChromeAdapter,
    _chrome_time_to_datetime,
    _datetime_to_chrome_time,
)


@pytest.fixture
def chrome_db(tmp_path):
    """Create a fake Chrome History database."""
    db_path = tmp_path / "History"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE TABLE urls ("
        "id INTEGER PRIMARY KEY, url TEXT, title TEXT, "
        "visit_count INTEGER, typed_count INTEGER, "
        "last_visit_time INTEGER, hidden INTEGER)"
    )
    conn.execute(
        "CREATE TABLE visits ("
        "id INTEGER PRIMARY KEY, url INTEGER, visit_time INTEGER, "
        "from_visit INTEGER, transition INTEGER, visit_duration INTEGER)"
    )

    # Insert test data
    # epoch for 2026-02-20 12:00:00 UTC
    dt1 = datetime(2026, 2, 20, 12, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 2, 21, 14, 30, 0, tzinfo=timezone.utc)
    t1 = _datetime_to_chrome_time(dt1)
    t2 = _datetime_to_chrome_time(dt2)

    conn.execute(
        "INSERT INTO urls VALUES (1, 'https://github.com', 'GitHub', 5, 2, ?, 0)",
        (t1,),
    )
    conn.execute(
        "INSERT INTO urls VALUES (2, 'https://example.com', 'Example', 1, 0, ?, 0)",
        (t2,),
    )
    conn.execute(
        "INSERT INTO visits VALUES (1, 1, ?, 0, 0, 1000)", (t1,)
    )
    conn.execute(
        "INSERT INTO visits VALUES (2, 2, ?, 0, 0, 500)", (t2,)
    )
    conn.commit()
    conn.close()
    return str(db_path)


def test_chrome_time_roundtrip():
    dt = datetime(2026, 2, 25, 10, 30, 0, tzinfo=timezone.utc)
    chrome_time = _datetime_to_chrome_time(dt)
    result = _chrome_time_to_datetime(chrome_time)
    assert abs((result - dt).total_seconds()) < 1


def test_search_all(chrome_db):
    adapter = ChromeAdapter(name="test", path=chrome_db)
    results = adapter.search()
    assert len(results) == 2
    # Most recent first
    assert "Example" in results[0].summary


def test_search_with_query(chrome_db):
    adapter = ChromeAdapter(name="test", path=chrome_db)
    results = adapter.search(query="github")
    assert len(results) == 1
    assert results[0].detail == "https://github.com"


def test_search_with_since(chrome_db):
    adapter = ChromeAdapter(name="test", path=chrome_db)
    since = datetime(2026, 2, 21, 0, 0, 0, tzinfo=timezone.utc)
    results = adapter.search(since=since)
    assert len(results) == 1
    assert "Example" in results[0].summary


def test_search_with_limit(chrome_db):
    adapter = ChromeAdapter(name="test", path=chrome_db)
    results = adapter.search(limit=1)
    assert len(results) == 1


def test_available(chrome_db):
    adapter = ChromeAdapter(name="test", path=chrome_db)
    assert adapter.available() is True


def test_not_available(tmp_path):
    adapter = ChromeAdapter(name="test", path=str(tmp_path / "nonexistent"))
    assert adapter.available() is False


def test_entry_fields(chrome_db):
    adapter = ChromeAdapter(name="test", path=chrome_db)
    results = adapter.search(query="github")
    entry = results[0]
    assert entry.source == "test"
    assert entry.kind == "url"
    assert entry.summary == "GitHub"
    assert entry.detail == "https://github.com"
    assert entry.timestamp is not None
