"""Tests for courier config management."""

import json

from guppi_courier import config


def test_load_config_missing(tmp_path, monkeypatch):
    """Missing config returns empty structure."""
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    cfg = config.load_config()
    assert cfg == {"default": None, "bots": {}}


def test_save_and_load_config(tmp_path, monkeypatch):
    """Round-trip save/load."""
    config_file = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", config_file)

    cfg = {"default": "test", "bots": {"test": {"name": "test_bot"}}}
    config.save_config(cfg)
    assert config.load_config() == cfg


def test_add_bot_first_becomes_default(tmp_path, monkeypatch):
    """First bot added becomes the default."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")

    config.add_bot("mybot", bot_name="my_telegram_bot")
    cfg = config.load_config()
    assert cfg["default"] == "mybot"
    assert cfg["bots"]["mybot"]["name"] == "my_telegram_bot"


def test_add_bot_explicit_default(tmp_path, monkeypatch):
    """Explicit default overrides existing."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")

    config.add_bot("first")
    config.add_bot("second", default=True)
    cfg = config.load_config()
    assert cfg["default"] == "second"


def test_remove_bot(tmp_path, monkeypatch):
    """Remove cleans up bot and resets default."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(config, "OFFSETS_DIR", tmp_path / "offsets")
    monkeypatch.setattr(config, "CHAT_IDS_DIR", tmp_path / "chat_ids")

    config.add_bot("a")
    config.add_bot("b")
    config.remove_bot("a")

    cfg = config.load_config()
    assert "a" not in cfg["bots"]
    assert cfg["default"] == "b"


def test_get_bot_default(tmp_path, monkeypatch):
    """get_bot with no name returns default."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")

    config.add_bot("mybot", bot_name="my_telegram_bot")
    name, bot_cfg = config.get_bot()
    assert name == "mybot"
    assert bot_cfg["name"] == "my_telegram_bot"


def test_get_bot_by_name(tmp_path, monkeypatch):
    """get_bot with explicit name."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")

    config.add_bot("a", bot_name="bot_a")
    config.add_bot("b", bot_name="bot_b")
    name, bot_cfg = config.get_bot("b")
    assert name == "b"
    assert bot_cfg["name"] == "bot_b"


def test_get_bot_not_found(tmp_path, monkeypatch):
    """get_bot raises for unknown bot."""
    monkeypatch.setattr(config, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE", tmp_path / "config.json")

    config.add_bot("a")
    try:
        config.get_bot("nope")
        assert False, "Should have raised"
    except RuntimeError as e:
        assert "not found" in str(e)


def test_offset_round_trip(tmp_path, monkeypatch):
    """Offset read/write."""
    monkeypatch.setattr(config, "OFFSETS_DIR", tmp_path / "offsets")
    assert config.get_offset("test") is None
    config.set_offset("test", 42)
    assert config.get_offset("test") == 42


def test_chat_id_round_trip(tmp_path, monkeypatch):
    """Chat ID read/write."""
    monkeypatch.setattr(config, "CHAT_IDS_DIR", tmp_path / "chat_ids")
    assert config.get_chat_id("test") is None
    config.set_chat_id("test", 12345)
    assert config.get_chat_id("test") == 12345


def test_get_inbox_path(tmp_path, monkeypatch):
    """Inbox path without today flag."""
    monkeypatch.setattr(config, "INBOX_DIR", tmp_path / "inbox")
    path = config.get_inbox_path("handoffs")
    assert path == tmp_path / "inbox" / "handoffs"


def test_get_inbox_path_today(tmp_path, monkeypatch):
    """Inbox path with today flag includes date."""
    from datetime import date

    monkeypatch.setattr(config, "INBOX_DIR", tmp_path / "inbox")
    path = config.get_inbox_path("handoffs", today=True)
    assert path == tmp_path / "inbox" / "handoffs" / date.today().isoformat()


def test_get_inbox_today_creates_dir(tmp_path, monkeypatch):
    """get_inbox_today creates the directory."""
    monkeypatch.setattr(config, "INBOX_DIR", tmp_path / "inbox")
    path = config.get_inbox_today("handoffs")
    assert path.is_dir()


def test_deduplicate_path_no_collision(tmp_path):
    """No collision returns original path."""
    dest = tmp_path / "message.md"
    assert config.deduplicate_path(dest) == dest


def test_deduplicate_path_one_collision(tmp_path):
    """One existing file gets (1) suffix."""
    (tmp_path / "message.md").write_text("first")
    dest = config.deduplicate_path(tmp_path / "message.md")
    assert dest == tmp_path / "message (1).md"


def test_deduplicate_path_multiple_collisions(tmp_path):
    """Multiple collisions increment correctly."""
    (tmp_path / "report.xlsx").write_text("first")
    (tmp_path / "report (1).xlsx").write_text("second")
    (tmp_path / "report (2).xlsx").write_text("third")
    dest = config.deduplicate_path(tmp_path / "report.xlsx")
    assert dest == tmp_path / "report (3).xlsx"


def test_deduplicate_path_no_extension(tmp_path):
    """Works with files that have no extension."""
    (tmp_path / "README").write_text("first")
    dest = config.deduplicate_path(tmp_path / "README")
    assert dest == tmp_path / "README (1)"
