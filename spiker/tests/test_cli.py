"""Tests for guppi-spiker CLI."""

import re

from typer.testing import CliRunner

from guppi_spiker.cli import app

runner = CliRunner()


def test_new_with_name(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["new", "my-spike", "--no-git"])
    assert result.exit_code == 0
    path = result.output.strip()
    assert "my-spike" in path
    assert re.match(r".*\d{4}-\d{2}-\d{2}-my-spike$", path)


def test_new_without_name(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["new", "--no-git"])
    assert result.exit_code == 0
    path = result.output.strip()
    # Should match YYYY-MM-DD-adjective-color-animal
    assert re.match(r".*\d{4}-\d{2}-\d{2}-\w+-\w+-\w+$", path)


def test_new_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["new", "test-spike", "--no-git"])
    from pathlib import Path
    assert Path(result.output.strip()).is_dir()


def test_new_with_git(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["new", "git-spike"])
    from pathlib import Path
    spike_path = Path(result.output.strip())
    assert (spike_path / ".git").is_dir()


def test_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No spikes found" in result.output


def test_list_shows_spikes(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-10-alpha").mkdir()
    (tmp_path / "2026-02-12-beta").mkdir()
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    assert len(lines) == 2
    assert "beta" in lines[0]  # most recent first
    assert "alpha" in lines[1]


def test_find_matches(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-caching").mkdir()
    (tmp_path / "2026-02-12-graphql-test").mkdir()
    result = runner.invoke(app, ["find", "redis"])
    assert result.exit_code == 0
    assert "redis-caching" in result.output


def test_find_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-caching").mkdir()
    result = runner.invoke(app, ["find", "nonexistent"])
    assert result.exit_code == 1


def test_find_case_insensitive(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-Redis-Caching").mkdir()
    result = runner.invoke(app, ["find", "redis"])
    assert result.exit_code == 0
    assert "Redis-Caching" in result.output


def test_path_returns_first_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-10-redis-old").mkdir()
    (tmp_path / "2026-02-12-redis-new").mkdir()
    result = runner.invoke(app, ["path", "redis"])
    assert result.exit_code == 0
    assert "redis-new" in result.output  # most recent
    assert result.output.strip().count("\n") == 0  # single line


def test_path_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["path", "nonexistent"])
    assert result.exit_code == 1


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "spiker" in result.output
    assert "guppi-spiker" in result.output
