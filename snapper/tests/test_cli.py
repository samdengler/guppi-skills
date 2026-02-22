"""Tests for guppi-snapper CLI."""

from typer.testing import CliRunner

from guppi_snapper.cli import app

runner = CliRunner()


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "snapper" in result.output
    assert "guppi-snapper" in result.output


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "CDP browser screenshots" in result.output


def test_start_help():
    result = runner.invoke(app, ["start", "--help"])
    assert result.exit_code == 0
    assert "--profile" in result.output
    assert "--port" in result.output


def test_capture_help():
    result = runner.invoke(app, ["capture", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.output
    assert "--viewport" in result.output
    assert "--wait" in result.output


def test_batch_help():
    result = runner.invoke(app, ["batch", "--help"])
    assert result.exit_code == 0
    assert "CONFIG_FILE" in result.output


def test_profile_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    result = runner.invoke(app, ["profile", "list"])
    assert result.exit_code == 0
    assert "No profiles found" in result.output


def test_profile_create(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    result = runner.invoke(app, ["profile", "create", "test-profile"])
    assert result.exit_code == 0
    assert "Created profile: test-profile" in result.output
    assert (tmp_path / "guppi" / "snapper" / "profiles" / "test-profile").is_dir()


def test_profile_create_duplicate(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    runner.invoke(app, ["profile", "create", "dupe"])
    result = runner.invoke(app, ["profile", "create", "dupe"])
    assert result.exit_code == 1
    assert "already exists" in result.output


def test_profile_delete(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    runner.invoke(app, ["profile", "create", "to-delete"])
    result = runner.invoke(app, ["profile", "delete", "to-delete", "--yes"])
    assert result.exit_code == 0
    assert "Deleted profile: to-delete" in result.output
    assert not (tmp_path / "guppi" / "snapper" / "profiles" / "to-delete").exists()


def test_profile_delete_not_found(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    result = runner.invoke(app, ["profile", "delete", "nonexistent", "--yes"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_profile_list_shows_profiles(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    runner.invoke(app, ["profile", "create", "alpha"])
    runner.invoke(app, ["profile", "create", "beta"])
    result = runner.invoke(app, ["profile", "list"])
    assert result.exit_code == 0
    assert "alpha" in result.output
    assert "beta" in result.output
