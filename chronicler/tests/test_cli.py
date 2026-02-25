"""Tests for CLI commands."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from guppi_chronicler import config
from guppi_chronicler.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def tmp_config(tmp_path, monkeypatch):
    """Redirect config to a temp directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_file = config_dir / "config.json"
    monkeypatch.setattr(config, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)
    return config_file


def test_source_list_empty():
    result = runner.invoke(app, ["source", "list"])
    assert result.exit_code == 0
    assert "No sources registered" in result.stdout


def test_source_add_and_list():
    result = runner.invoke(app, ["source", "add", "myterm", "--type", "terminal"])
    assert result.exit_code == 0
    assert "registered" in result.stdout

    result = runner.invoke(app, ["source", "list"])
    assert "myterm" in result.stdout
    assert "terminal" in result.stdout


def test_source_add_unknown_type():
    result = runner.invoke(app, ["source", "add", "foo", "--type", "unknown"])
    assert result.exit_code == 1
    assert "Unknown source type" in result.stdout


def test_source_remove():
    runner.invoke(app, ["source", "add", "myterm", "--type", "terminal"])
    result = runner.invoke(app, ["source", "remove", "myterm"])
    assert result.exit_code == 0
    assert "removed" in result.stdout


def test_source_remove_nonexistent():
    result = runner.invoke(app, ["source", "remove", "nope"])
    assert result.exit_code == 1


def test_source_enable_disable():
    runner.invoke(app, ["source", "add", "myterm", "--type", "terminal"])

    result = runner.invoke(app, ["source", "disable", "myterm"])
    assert result.exit_code == 0
    assert "disabled" in result.stdout

    result = runner.invoke(app, ["source", "enable", "myterm"])
    assert result.exit_code == 0
    assert "enabled" in result.stdout


def test_search_no_sources():
    result = runner.invoke(app, ["search"])
    assert result.exit_code == 0
    assert "No sources configured" in result.stdout


def test_search_invalid_date():
    runner.invoke(app, ["source", "add", "myterm", "--type", "terminal"])
    result = runner.invoke(app, ["search", "--since", "not a date"])
    assert result.exit_code == 1
    assert "Cannot parse date" in result.stdout


def test_search_nonexistent_source():
    result = runner.invoke(app, ["search", "--source", "nope"])
    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_source_init_nonexistent():
    result = runner.invoke(app, ["source", "init", "nope"])
    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_skill_show(monkeypatch):
    # Point to the real SKILL.md in the project root
    skill_md = Path(__file__).parent.parent / "SKILL.md"
    monkeypatch.setattr(
        "guppi_chronicler.cli._get_skill_md_path", lambda: skill_md
    )
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "chronicler" in result.stdout
