"""Tests for date parsing module."""

from datetime import datetime, timezone

import pytest

from guppi_chronicler.dates import parse_date


def test_today():
    result = parse_date("today")
    now = datetime.now(tz=timezone.utc)
    assert result.year == now.year
    assert result.month == now.month
    assert result.day == now.day
    assert result.hour == 0
    assert result.minute == 0


def test_yesterday():
    result = parse_date("yesterday")
    now = datetime.now(tz=timezone.utc)
    # Yesterday should be before today at midnight
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    assert result < today_midnight


def test_n_days_ago():
    result = parse_date("3 days ago")
    now = datetime.now(tz=timezone.utc)
    # Should be roughly 3 days before now
    diff = now - result
    assert 2.9 < diff.total_seconds() / 86400 < 3.1


def test_n_hours_ago():
    result = parse_date("2 hours ago")
    now = datetime.now(tz=timezone.utc)
    diff = now - result
    assert 1.9 < diff.total_seconds() / 3600 < 2.1


def test_n_weeks_ago():
    result = parse_date("1 week ago")
    now = datetime.now(tz=timezone.utc)
    diff = now - result
    assert 6.9 < diff.total_seconds() / 86400 < 7.1


def test_last_week():
    result = parse_date("last week")
    now = datetime.now(tz=timezone.utc)
    diff = now - result
    assert 6.9 < diff.total_seconds() / 86400 < 7.1


def test_this_week():
    result = parse_date("this week")
    # Should be Monday of current week at midnight
    assert result.hour == 0
    assert result.weekday() == 0  # Monday


def test_this_month():
    result = parse_date("this month")
    now = datetime.now(tz=timezone.utc)
    assert result.day == 1
    assert result.month == now.month


def test_iso_date():
    result = parse_date("2026-02-25")
    assert result.year == 2026
    assert result.month == 2
    assert result.day == 25


def test_iso_datetime():
    result = parse_date("2026-02-25T14:30:00")
    assert result.year == 2026
    assert result.hour == 14
    assert result.minute == 30


def test_invalid_date():
    with pytest.raises(ValueError, match="Cannot parse date"):
        parse_date("not a date")


def test_case_insensitive():
    result = parse_date("Yesterday")
    assert result is not None


def test_whitespace_handling():
    result = parse_date("  today  ")
    assert result is not None
