"""Tests for guppi-courier CLI"""

from typer.testing import CliRunner

from guppi_courier.cli import app

runner = CliRunner()


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Telegram-based messaging" in result.output


def test_receive_help():
    result = runner.invoke(app, ["receive", "--help"])
    assert result.exit_code == 0
    assert "--bot" in result.output
    assert "--output" in result.output
    assert "--keep" in result.output


def test_send_help():
    result = runner.invoke(app, ["send", "--help"])
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


def test_inbox_default_bot(tmp_path, monkeypatch):
    """inbox command prints the inbox path for the default bot."""
    from guppi_courier import config

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(config, "INBOX_DIR", tmp_path / "inbox")
    config.add_bot("handoffs", bot_name="test_bot")

    result = runner.invoke(app, ["inbox"])
    assert result.exit_code == 0
    assert "inbox/handoffs" in result.output


def test_inbox_today(tmp_path, monkeypatch):
    """inbox --today appends today's date."""
    from datetime import date

    from guppi_courier import config

    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(config, "INBOX_DIR", tmp_path / "inbox")
    config.add_bot("handoffs", bot_name="test_bot")

    result = runner.invoke(app, ["inbox", "--today"])
    assert result.exit_code == 0
    assert date.today().isoformat() in result.output


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "courier" in result.output
