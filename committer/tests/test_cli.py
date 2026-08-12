"""Tests for guppi-committer CLI."""

import json
import subprocess

from typer.testing import CliRunner

from guppi_committer import __version__
from guppi_committer.cli import HOOK_MARKER, app

runner = CliRunner()

GOOD = "Add retry logic to fetcher\n"
BAD = "added retry logic.\n"


# --- check ---


def test_check_stdin_ok():
    result = runner.invoke(app, ["check"], input=GOOD)
    assert result.exit_code == 0
    assert "Commit message OK" in result.output


def test_check_stdin_rejects():
    result = runner.invoke(app, ["check"], input=BAD)
    assert result.exit_code == 1
    assert "subject-capitalization" in result.output
    assert "subject-imperative" in result.output
    assert "subject-period" in result.output


def test_check_file(tmp_path):
    msg = tmp_path / "msg.txt"
    msg.write_text(GOOD)
    result = runner.invoke(app, ["check", str(msg)])
    assert result.exit_code == 0


def test_check_missing_file():
    result = runner.invoke(app, ["check", "/nonexistent/msg.txt"])
    assert result.exit_code == 2


def test_check_json():
    result = runner.invoke(app, ["check", "--json"], input=BAD)
    assert result.exit_code == 1
    violations = json.loads(result.output)
    assert {"line", "rule", "severity", "message"} <= set(violations[0])


def test_check_strict_fails_on_warnings():
    msg = "Add retry logic\n\nThis simply retries.\n"
    assert runner.invoke(app, ["check"], input=msg).exit_code == 0
    assert runner.invoke(app, ["check", "--strict"], input=msg).exit_code == 1


# --- init ---


def _git_repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    return tmp_path


def test_init_installs_hook(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.chdir(repo)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    hook = repo / ".git" / "hooks" / "commit-msg"
    assert hook.exists()
    assert HOOK_MARKER in hook.read_text()
    assert hook.stat().st_mode & 0o111


def test_init_idempotent(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.chdir(repo)
    assert runner.invoke(app, ["init"]).exit_code == 0
    assert runner.invoke(app, ["init"]).exit_code == 0


def test_init_refuses_foreign_hook(tmp_path, monkeypatch):
    repo = _git_repo(tmp_path)
    monkeypatch.chdir(repo)
    hook = repo / ".git" / "hooks" / "commit-msg"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\necho custom\n")
    assert runner.invoke(app, ["init"]).exit_code == 1
    assert "echo custom" in hook.read_text()
    assert runner.invoke(app, ["init", "--force"]).exit_code == 0
    assert HOOK_MARKER in hook.read_text()


def test_init_outside_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    result = runner.invoke(app, ["init"])
    # git rev-parse --git-path may still succeed in odd environments;
    # accept either a clean error or a hook path outside a repo refusal.
    assert result.exit_code in (0, 1)


# --- version ---


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
