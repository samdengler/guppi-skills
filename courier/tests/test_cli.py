"""Tests for guppi-courier CLI"""

from typer.testing import CliRunner

from guppi_courier.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Telegram-based messaging" in result.output


def test_pull_help():
    result = runner.invoke(app, ["pull", "--help"])
    assert result.exit_code == 0
    assert "--bot" in result.output
    assert "--output" in result.output
    assert "--keep" in result.output


def test_push_help():
    result = runner.invoke(app, ["push", "--help"])
    assert result.exit_code == 0
    assert "--bot" in result.output
    assert "--file" in result.output


def test_peek_help():
    result = runner.invoke(app, ["peek", "--help"])
    assert result.exit_code == 0
    assert "--bot" in result.output


def test_bots_no_config(tmp_path, monkeypatch):
    """bots command with no config shows helpful message."""
    monkeypatch.setattr("guppi_courier.config.CONFIG_FILE", tmp_path / "config.json")
    result = runner.invoke(app, ["bots"])
    assert result.exit_code == 0
    assert "No bots configured" in result.output


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "courier" in result.output
