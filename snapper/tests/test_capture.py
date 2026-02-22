"""Tests for capture module."""

from guppi_snapper.capture import parse_viewport


def test_parse_viewport_standard():
    assert parse_viewport("1400x1092") == (1400, 1092)


def test_parse_viewport_small():
    assert parse_viewport("800x600") == (800, 600)


def test_parse_viewport_uppercase_x():
    assert parse_viewport("1920X1080") == (1920, 1080)


def test_parse_viewport_invalid_format():
    from typer import Exit
    import pytest
    with pytest.raises((Exit, SystemExit)):
        parse_viewport("invalid")


def test_parse_viewport_non_numeric():
    from typer import Exit
    import pytest
    with pytest.raises((Exit, SystemExit)):
        parse_viewport("abcxdef")


def test_parse_viewport_missing_dimension():
    from typer import Exit
    import pytest
    with pytest.raises((Exit, SystemExit)):
        parse_viewport("1400")
