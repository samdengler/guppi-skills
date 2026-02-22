"""Tests for XDG paths module."""

from pathlib import Path


def test_config_dir_default(monkeypatch):
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    from guppi_snapper.paths import config_dir
    result = config_dir()
    assert result == Path.home() / ".config" / "guppi" / "snapper"


def test_config_dir_custom(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/myconfig")
    from guppi_snapper.paths import config_dir
    result = config_dir()
    assert result == Path("/tmp/myconfig/guppi/snapper")


def test_data_dir_default(monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    from guppi_snapper.paths import data_dir
    result = data_dir()
    assert result == Path.home() / ".local" / "share" / "guppi" / "snapper"


def test_data_dir_custom(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/mydata")
    from guppi_snapper.paths import data_dir
    result = data_dir()
    assert result == Path("/tmp/mydata/guppi/snapper")


def test_profiles_dir(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/mydata")
    from guppi_snapper.paths import profiles_dir
    assert profiles_dir() == Path("/tmp/mydata/guppi/snapper/profiles")


def test_extensions_dir(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/mydata")
    from guppi_snapper.paths import extensions_dir
    assert extensions_dir() == Path("/tmp/mydata/guppi/snapper/extensions")


def test_profile_path(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/mydata")
    from guppi_snapper.paths import profile_path
    assert profile_path("default") == Path("/tmp/mydata/guppi/snapper/profiles/default")
    assert profile_path("myproject") == Path("/tmp/mydata/guppi/snapper/profiles/myproject")


def test_state_file(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/mydata")
    from guppi_snapper.paths import state_file
    assert state_file() == Path("/tmp/mydata/guppi/snapper/chromium.json")


def test_config_file(monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", "/tmp/myconfig")
    from guppi_snapper.paths import config_file
    assert config_file() == Path("/tmp/myconfig/guppi/snapper/config.toml")
