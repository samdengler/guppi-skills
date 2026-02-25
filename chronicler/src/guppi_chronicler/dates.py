"""Natural language and ISO 8601 date parsing."""

import re
from datetime import datetime, timedelta, timezone


def parse_date(text: str) -> datetime:
    """Parse a date string (natural language or ISO 8601) into a datetime.

    Supported natural language:
        today, yesterday
        N days/hours/weeks/months ago
        last week, last month
        this week, this month

    Falls back to datetime.fromisoformat() for ISO 8601 strings.

    Raises ValueError if the string can't be parsed.
    """
    text = text.strip().lower()
    now = datetime.now(tz=timezone.utc)

    # Simple keywords
    if text == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    if text == "yesterday":
        yesterday = now - timedelta(days=1)
        return yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    if text == "now":
        return now

    # "N <unit> ago" patterns
    ago_match = re.match(r"(\d+)\s+(hour|day|week|month)s?\s+ago", text)
    if ago_match:
        n = int(ago_match.group(1))
        unit = ago_match.group(2)
        if unit == "hour":
            return now - timedelta(hours=n)
        elif unit == "day":
            return now - timedelta(days=n)
        elif unit == "week":
            return now - timedelta(weeks=n)
        elif unit == "month":
            return now - timedelta(days=n * 30)

    # "last <period>"
    if text == "last week":
        return now - timedelta(weeks=1)
    if text == "last month":
        return now - timedelta(days=30)

    # "this <period>" — start of current period
    if text == "this week":
        # Monday of current week
        days_since_monday = now.weekday()
        monday = now - timedelta(days=days_since_monday)
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)
    if text == "this month":
        return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Fallback: ISO 8601
    try:
        parsed = datetime.fromisoformat(text)
        # Add UTC timezone if naive
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        pass

    raise ValueError(
        f"Cannot parse date: '{text}'. "
        "Try: 'yesterday', '3 days ago', 'last week', or ISO 8601 (2026-02-25)"
    )
