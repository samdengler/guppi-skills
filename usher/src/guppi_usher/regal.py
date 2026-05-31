"""Regal (regmovies.com) provider.

Pure parsing helpers (``parse_seat_plan``, ``parse_showtimes``) are testable
against captured fixtures. Network access runs through the browser bridge so it
inherits the user's authenticated, Cloudflare-cleared session.
"""

from __future__ import annotations

import json
import re
from datetime import time as _time
from typing import Optional

from guppi_usher.ranking import Seat, Showtime

BASE = "https://www.regmovies.com"


# --------------------------------------------------------------------------- #
# URL helpers
# --------------------------------------------------------------------------- #
def movie_showtimes_url(slug: str, theatre_code: str) -> str:
    return f"{BASE}/movies/{slug}?selected={theatre_code}"


def seat_page_url(slug: str, session_id: str, theatre_code: str, date: str) -> str:
    """Deep link to the seat-selection page. ``date`` is MM-DD-YYYY."""
    return f"{BASE}/movies/{slug}?id={session_id}&site={theatre_code}&date={date}"


def seat_plan_url(theatre_code: str, session_id: str) -> str:
    return f"{BASE}/api/GetSeatPlan?theatreCode={theatre_code}&sessionId={session_id}"


# --------------------------------------------------------------------------- #
# Pure parsing
# --------------------------------------------------------------------------- #
def parse_seat_plan(payload: dict) -> tuple[list[Seat], str]:
    """Flatten a GetSeatPlan payload into (seats, screen_label).

    Screen label is not in this payload; callers may pass it through separately.
    """
    seats: list[Seat] = []
    layout = payload.get("SeatLayoutData", {})
    for area in layout.get("Areas", []):
        area_name = area.get("Description", "Standard")
        for row in area.get("Rows", []):
            row_name = row.get("PhysicalName", "")
            for s in row.get("Seats", []):
                pos = s.get("Position", {})
                seats.append(
                    Seat(
                        row=row_name,
                        col=int(pos.get("ColumnIndex", 0)),
                        id=str(s.get("Id", "")),
                        status=int(s.get("Status", 0)),
                        area=area_name,
                    )
                )
    return seats, ""


_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(am|pm)$", re.IGNORECASE)


def parse_clock(text: str) -> Optional[_time]:
    """Parse '7:15pm' / '12:10am' into a datetime.time."""
    m = _TIME_RE.match(text.strip())
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    if ampm == "pm" and hour != 12:
        hour += 12
    elif ampm == "am" and hour == 12:
        hour = 0
    return _time(hour, minute)


# --------------------------------------------------------------------------- #
# Browser-backed access (live)
# --------------------------------------------------------------------------- #
def fetch_seat_plan(theatre_code: str, session_id: str) -> list[Seat]:
    """Fetch + parse the seat plan via the active browser session.

    The active Chrome tab must be on regmovies.com (any page) for cookies and
    Cloudflare clearance to apply.
    """
    from guppi_usher import browser

    raw = browser.fetch_json(seat_plan_url(theatre_code, session_id))
    payload = json.loads(raw)
    seats, _ = parse_seat_plan(payload)
    return seats


# JS that scrapes the rendered showtimes for a theatre into structured data.
# Showtime session ids are not on the buttons, so this returns the button ids
# (show<idx>time<n>); the caller clicks one to obtain the session id from the URL.
_SHOWTIMES_JS = r"""
(() => {
  const out = [];
  document.querySelectorAll('button[id^="show"]').forEach(b => {
    const label = (b.getAttribute('aria-label') || b.textContent || '').trim();
    const m = label.match(/(\d{1,2}:\d{2}(am|pm))/i);
    if (m) out.push({ btnId: b.id, time: m[1] });
  });
  return JSON.stringify(out);
})()
"""


def fetch_showtimes_raw() -> list[dict]:
    """Return [{btnId, time}] for the currently-loaded movie/theatre page.

    NOTE: format association per showtime is still approximate from the DOM and
    is tracked for hardening (guppi-skills-tmy). Navigation to the movie page is
    the caller's responsibility.
    """
    from guppi_usher import browser

    return json.loads(browser.run_js(_SHOWTIMES_JS))


def current_session_id() -> Optional[str]:
    """Read id=<sessionId> from the active tab's URL after a showtime click."""
    from guppi_usher import browser

    url = browser.run_js("window.location.href")
    m = re.search(r"[?&]id=(\d+)", url)
    return m.group(1) if m else None
