"""Tests for capture module."""

import pytest

from guppi_snapper.capture import find_existing_page, parse_viewport


def test_parse_viewport_standard():
    assert parse_viewport("1400x1092") == (1400, 1092)


def test_parse_viewport_new_default():
    assert parse_viewport("1400x1365") == (1400, 1365)


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
    with pytest.raises((Exit, SystemExit)):
        parse_viewport("1400")


class _FakePage:
    def __init__(self, url):
        self.url = url


def test_find_existing_page_match():
    class FakeContext:
        pages = [_FakePage("https://docs.google.com/spreadsheets/d/123"), _FakePage("https://example.com")]
    page = find_existing_page(FakeContext(), "spreadsheets")
    assert page is not None
    assert "spreadsheets" in page.url


def test_find_existing_page_no_match():
    class FakeContext:
        pages = [_FakePage("https://example.com")]
    page = find_existing_page(FakeContext(), "spreadsheets")
    assert page is None


def test_find_existing_page_empty():
    class FakeContext:
        pages = []
    page = find_existing_page(FakeContext(), "anything")
    assert page is None


def test_resize_image_calls_magick(monkeypatch):
    """Test that resize_image shells out to magick with correct args."""
    from unittest.mock import MagicMock
    from guppi_snapper import capture

    mock_run = MagicMock(return_value=MagicMock(returncode=0))
    monkeypatch.setattr(capture, "subprocess", MagicMock(run=mock_run))

    capture.resize_image("/tmp/test.png", 1120, 1092)

    mock_run.assert_called_once()
    args = mock_run.call_args[0][0]
    assert args[0] == "magick"
    assert "/tmp/test.png" in args
    assert "1120x1092" in args
