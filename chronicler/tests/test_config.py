"""Tests for config module."""

import json

import pytest

from guppi_chronicler import config


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    """Redirect config to a temp directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)
    return config_file


def test_load_empty():
    result = config.load_config()
    assert result == {"sources": {}}


def test_add_source():
    config.add_source("chrome", "chrome")
    sources = config.get_sources()
    assert "chrome" in sources
    assert sources["chrome"]["type"] == "chrome"
    assert sources["chrome"]["enabled"] is True
    assert sources["chrome"]["path"] is None


def test_add_source_with_path():
    config.add_source("chrome", "chrome", "/custom/path")
    sources = config.get_sources()
    assert sources["chrome"]["path"] == "/custom/path"


def test_add_duplicate_raises():
    config.add_source("chrome", "chrome")
    with pytest.raises(ValueError, match="already exists"):
        config.add_source("chrome", "chrome")


def test_remove_source():
    config.add_source("chrome", "chrome")
    config.remove_source("chrome")
    assert config.get_sources() == {}


def test_remove_nonexistent_raises():
    with pytest.raises(ValueError, match="not found"):
        config.remove_source("nope")


def test_enable_disable():
    config.add_source("chrome", "chrome")
    config.set_source_enabled("chrome", False)
    assert config.get_source("chrome")["enabled"] is False

    config.set_source_enabled("chrome", True)
    assert config.get_source("chrome")["enabled"] is True


def test_enable_nonexistent_raises():
    with pytest.raises(ValueError, match="not found"):
        config.set_source_enabled("nope", True)


def test_get_enabled_sources():
    config.add_source("chrome", "chrome")
    config.add_source("terminal", "terminal")
    config.set_source_enabled("chrome", False)

    enabled = config.get_enabled_sources()
    assert "terminal" in enabled
    assert "chrome" not in enabled


def test_get_source_returns_none():
    assert config.get_source("nope") is None
