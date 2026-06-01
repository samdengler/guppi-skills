"""Pure ranking logic for usher — no I/O, fully unit-testable.

Covers: format ranking (chain-aware), time-window filtering, contiguous-seat
finding, center scoring, and saved-pick matching.

Seat status (from regmovies GetSeatPlan): 0 = available, 1 = taken,
3 & 7 = accessible/blocked (treated as unavailable).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time as _time
from typing import Optional

AVAILABLE = 0


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Seat:
    row: str            # PhysicalName, e.g. "K"
    col: int            # Position.ColumnIndex (use for centeredness)
    id: str             # seat number shown to the user (match saved picks on this)
    status: int         # 0 = available
    area: str = "Standard"

    @property
    def available(self) -> bool:
        return self.status == AVAILABLE


@dataclass
class Showtime:
    time: _time         # local start time
    fmt: str            # raw format label, e.g. "IMAX", "Standard", "ScreenX"
    session_id: str = ""
    screen: str = ""    # Regal "Screen N" label if known
    theatre_code: str = ""

    def __str__(self) -> str:
        return f"{self.time.strftime('%-I:%M%p').lower()} {self.fmt}"


@dataclass
class SeatGroup:
    row: str
    seats: list[Seat]
    center_distance: float          # |window center - row center|
    row_rank: int = 0               # lower = more preferred row

    @property
    def labels(self) -> list[str]:
        return [f"{s.row}{s.id}" for s in self.seats]


# --------------------------------------------------------------------------- #
# Format ranking
# --------------------------------------------------------------------------- #
# Lower index = more preferred. Formats absent from a chain's map fall to the
# end. A value of None means "exclude" (e.g. ScreenX).
_REGAL_PRIORITY = {
    "imax": 0,
    "rpx": 1,
    "4dx": 2,        # gated: only kept for action movies
    "screenx": None,  # never
    "standard": 4,
    "vip": 5,
    "recliner": 5,
}
_AMC_PRIORITY = {
    "dolby": 0,
    "imax": 1,
    "standard": 4,
}
_CHAIN_PRIORITY = {"regal": _REGAL_PRIORITY, "amc": _AMC_PRIORITY}

_DEFAULT_RANK = 9  # known-but-unprioritized format


def _norm(fmt: str) -> str:
    return "".join(c for c in fmt.lower() if c.isalnum())


def format_rank(fmt: str, chain: str = "regal", is_action: bool = False) -> Optional[int]:
    """Return a sort rank for a format, or None if it should be excluded.

    - ScreenX is always excluded (user dislikes it).
    - 4DX is excluded unless ``is_action`` (user likes 4DX only for action).
    """
    table = _CHAIN_PRIORITY.get(chain.lower(), _REGAL_PRIORITY)
    key = _norm(fmt)
    matched = None
    for name, rank in table.items():
        if name in key:
            matched = (name, rank)
            break
    if matched is None:
        return _DEFAULT_RANK
    name, rank = matched
    if rank is None:
        return None
    if name == "4dx" and not is_action:
        return None
    return rank


def rank_showtimes(
    showtimes: list[Showtime],
    chain: str = "regal",
    is_action: bool = False,
) -> list[Showtime]:
    """Drop excluded formats, then sort by (format rank, time). Format first."""
    ranked = []
    for s in showtimes:
        r = format_rank(s.fmt, chain, is_action)
        if r is None:
            continue
        ranked.append((r, s.time, s))
    ranked.sort(key=lambda t: (t[0], t[1]))
    return [s for _, _, s in ranked]


# --------------------------------------------------------------------------- #
# Time-window filtering
# --------------------------------------------------------------------------- #
def filter_time(
    showtimes: list[Showtime],
    after: Optional[_time] = None,
    before: Optional[_time] = None,
) -> list[Showtime]:
    """Keep showtimes within [after, before] (inclusive bounds, either optional)."""
    out = []
    for s in showtimes:
        if after is not None and s.time < after:
            continue
        if before is not None and s.time > before:
            continue
        out.append(s)
    return out


# --------------------------------------------------------------------------- #
# Seat geometry
# --------------------------------------------------------------------------- #
def row_center(row_seats: list[Seat]) -> float:
    """Center column of a row = midpoint of its column span (all seats, not just open)."""
    cols = [s.col for s in row_seats]
    if not cols:
        return 0.0
    return (min(cols) + max(cols)) / 2


def best_contiguous_in_row(row_seats: list[Seat], n: int) -> Optional[SeatGroup]:
    """Best run of ``n`` adjacent available seats in one row, closest to row center.

    Adjacency is by ColumnIndex (consecutive columns differ by 1), so a run does
    not span an aisle gap. Returns None if no such run exists.
    """
    if n <= 0 or not row_seats:
        return None
    center = row_center(row_seats)
    available = sorted((s for s in row_seats if s.available), key=lambda s: s.col)

    best: Optional[SeatGroup] = None
    run: list[Seat] = []
    for seat in available:
        if run and seat.col == run[-1].col + 1:
            run.append(seat)
        else:
            run = [seat]
        if len(run) >= n:
            window = run[-n:]
            win_center = (window[0].col + window[-1].col) / 2
            dist = abs(win_center - center)
            if best is None or dist < best.center_distance:
                best = SeatGroup(row=window[0].row, seats=list(window), center_distance=dist)
    return best


def find_best_seats(
    seats: list[Seat],
    n: int,
    row_priority: Optional[list[str]] = None,
) -> list[SeatGroup]:
    """Find contiguous N-seat groups across all rows, ranked best-first.

    If ``row_priority`` is given (ordered best→worst row letters), groups are
    ranked by (row rank, center distance). Otherwise ranked by center distance
    with a gentle preference for middle-to-back rows.
    """
    rows: dict[str, list[Seat]] = {}
    for s in seats:
        rows.setdefault(s.row, []).append(s)

    # Default row ordering: middle-to-back center is generally best. Rows are
    # lettered A (front) .. back; prefer rows around 60% toward the back.
    ordered_rows = _row_order(list(rows.keys()))
    rank_of = {r: i for i, r in enumerate(row_priority or ordered_rows)}
    fallback_rank = len(rank_of)

    groups: list[SeatGroup] = []
    for row, row_seats in rows.items():
        grp = best_contiguous_in_row(row_seats, n)
        if grp is None:
            continue
        grp.row_rank = rank_of.get(row, fallback_rank)
        groups.append(grp)

    groups.sort(key=lambda g: (g.row_rank, g.center_distance))
    return groups


def _row_order(row_letters: list[str]) -> list[str]:
    """Order rows by desirability: middle-to-back first.

    Rows are single letters A(front)..back. Target ~60% of the way back.
    """
    rows = sorted(row_letters)  # A, B, C, ... front to back
    if not rows:
        return []
    n = len(rows)
    target = (n - 1) * 0.6
    return sorted(rows, key=lambda r: abs(rows.index(r) - target))


# --------------------------------------------------------------------------- #
# Saved-pick matching
# --------------------------------------------------------------------------- #
@dataclass
class PickResult:
    available: bool
    seats: list[Seat] = field(default_factory=list)
    note: str = ""


def match_saved_pick(seats: list[Seat], pick: list[tuple[str, str]]) -> PickResult:
    """Check whether a saved pick (list of (row, seat_id)) is fully available.

    Returns the matched seats when all are open; otherwise reports unavailable
    so the caller can fall back to ``find_best_seats``.
    """
    by_key = {(s.row, s.id): s for s in seats}
    matched = [by_key.get(key) for key in pick]
    if all(s is not None and s.available for s in matched):
        return PickResult(available=True, seats=[s for s in matched if s])
    taken = [f"{r}{i}" for (r, i), s in zip(pick, matched) if s is None or not s.available]
    return PickResult(available=False, note=f"unavailable: {', '.join(taken)}")
