"""Tests for browser module."""

import json

from guppi_snapper.browser import is_port_in_use, load_state, save_state


def test_is_port_in_use_closed():
    # Port 19999 should not be in use
    assert is_port_in_use(19999) is False


def test_save_and_load_state(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    save_state(12345, 9222, "default")

    state = load_state()
    assert state is not None
    assert state["pid"] == 12345
    assert state["port"] == 9222
    assert state["profile"] == "default"


def test_load_state_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert load_state() is None


def test_load_state_corrupt(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    sf = tmp_path / "guppi" / "snapper" / "chromium.json"
    sf.parent.mkdir(parents=True)
    sf.write_text("not json")
    assert load_state() is None


def test_save_state_creates_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    save_state(1, 9222, "test")
    sf = tmp_path / "guppi" / "snapper" / "chromium.json"
    assert sf.exists()
    data = json.loads(sf.read_text())
    assert data["pid"] == 1


def test_stop_chromium_cleans_state_file(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    save_state(99999, 9222, "default")
    sf = tmp_path / "guppi" / "snapper" / "chromium.json"
    assert sf.exists()

    from guppi_snapper.browser import stop_chromium
    # PID 99999 should not exist, so SIGTERM will raise ProcessLookupError
    stop_chromium(99999, sf)
    assert not sf.exists()
