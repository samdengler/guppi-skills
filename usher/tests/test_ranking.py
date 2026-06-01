"""Unit tests for usher's pure ranking + parsing logic."""

from datetime import time

from guppi_usher import regal
from guppi_usher.ranking import (
    Seat,
    Showtime,
    best_contiguous_in_row,
    filter_time,
    find_best_seats,
    format_rank,
    match_saved_pick,
    rank_showtimes,
    row_center,
)


# --------------------------------------------------------------------------- #
# format ranking
# --------------------------------------------------------------------------- #
def test_imax_beats_standard():
    assert format_rank("IMAX") < format_rank("Standard")


def test_screenx_excluded():
    assert format_rank("ScreenX") is None
    assert format_rank("ScreenX with Closed Caption") is None


def test_4dx_only_for_action():
    assert format_rank("4DX", is_action=False) is None
    assert format_rank("4DX", is_action=True) is not None
    # even for action, IMAX still preferred over 4DX
    assert format_rank("IMAX", is_action=True) < format_rank("4DX", is_action=True)


def test_amc_prefers_dolby():
    assert format_rank("Dolby Cinema", chain="amc") < format_rank("Standard", chain="amc")


def test_rank_showtimes_format_first_then_time():
    shows = [
        Showtime(time(18, 0), "Standard"),
        Showtime(time(22, 0), "IMAX"),
        Showtime(time(19, 0), "ScreenX"),   # dropped
        Showtime(time(20, 0), "IMAX"),
    ]
    ranked = rank_showtimes(shows)
    # ScreenX dropped; IMAX first (earlier IMAX before later IMAX); Standard last
    assert [(s.fmt, s.time) for s in ranked] == [
        ("IMAX", time(20, 0)),
        ("IMAX", time(22, 0)),
        ("Standard", time(18, 0)),
    ]


# --------------------------------------------------------------------------- #
# time filtering
# --------------------------------------------------------------------------- #
def test_filter_after():
    shows = [Showtime(time(17, 0), "Standard"), Showtime(time(18, 30), "Standard")]
    out = filter_time(shows, after=time(18, 0))
    assert [s.time for s in out] == [time(18, 30)]


# --------------------------------------------------------------------------- #
# seat geometry
# --------------------------------------------------------------------------- #
def _row(letter, cols, taken=()):
    return [Seat(letter, c, str(c), 1 if c in taken else 0) for c in cols]


def test_row_center():
    assert row_center(_row("A", range(1, 21))) == 10.5


def test_contiguous_prefers_center():
    # all open in a 1..20 row, want 2 → center pair ~ cols 10-11
    grp = best_contiguous_in_row(_row("F", range(1, 21)), 2)
    assert grp is not None
    assert [s.col for s in grp.seats] == [10, 11]


def test_contiguous_respects_gaps():
    # only cols 1,2 and 18,19 open (center taken); a 2-run must come from an edge
    row = _row("L", range(1, 20), taken=set(range(3, 18)))
    grp = best_contiguous_in_row(row, 2)
    assert grp is not None
    assert {s.col for s in grp.seats} in ({1, 2}, {18, 19})


def test_contiguous_none_when_no_run():
    # every other seat taken → no two adjacent
    row = _row("M", range(1, 11), taken={2, 4, 6, 8, 10})
    assert best_contiguous_in_row(row, 2) is None


def test_find_best_seats_respects_row_priority():
    seats = _row("J", range(1, 21)) + _row("A", range(1, 21))
    groups = find_best_seats(seats, 2, row_priority=["J", "A"])
    assert groups[0].row == "J"


# --------------------------------------------------------------------------- #
# saved-pick matching
# --------------------------------------------------------------------------- #
def test_saved_pick_available():
    seats = _row("K", range(1, 21))
    res = match_saved_pick(seats, [("K", "15"), ("K", "16")])
    assert res.available
    assert [s.id for s in res.seats] == ["15", "16"]


def test_saved_pick_taken_falls_back():
    seats = _row("L", range(1, 21), taken={8})
    res = match_saved_pick(seats, [("L", "8")])
    assert not res.available
    assert "L8" in res.note


# --------------------------------------------------------------------------- #
# regal parsing
# --------------------------------------------------------------------------- #
def test_parse_seat_plan():
    payload = {
        "SeatLayoutData": {
            "Areas": [
                {
                    "Description": "Standard",
                    "Rows": [
                        {
                            "PhysicalName": "K",
                            "Seats": [
                                {"Position": {"ColumnIndex": 0}, "Id": "1", "Status": 0},
                                {"Position": {"ColumnIndex": 1}, "Id": "2", "Status": 1},
                            ],
                        }
                    ],
                }
            ]
        }
    }
    seats, _ = regal.parse_seat_plan(payload)
    assert len(seats) == 2
    assert seats[0].row == "K" and seats[0].id == "1" and seats[0].available
    assert not seats[1].available


def test_parse_clock():
    assert regal.parse_clock("7:15pm") == time(19, 15)
    assert regal.parse_clock("12:10am") == time(0, 10)
    assert regal.parse_clock("12:30pm") == time(12, 30)
    assert regal.parse_clock("nope") is None
