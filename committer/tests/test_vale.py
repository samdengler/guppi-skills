"""Tests for the Vale integration."""

import json
import subprocess
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from guppi_committer import vale
from guppi_committer.cli import app

runner = CliRunner()

GOOD = "Add retry logic to fetcher\n"

ALERT = {
    "Check": "Google.Simply",
    "Line": 3,
    "Message": "Remove 'simply'.",
    "Severity": "warning",
}


def _vale_proc(returncode=1, stdout=None, stderr=""):
    if stdout is None:
        stdout = json.dumps({"COMMIT_EDITMSG.md": [ALERT]})
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


# --- vale.run ---


def test_run_maps_alerts():
    with patch("guppi_committer.vale.subprocess.run", return_value=_vale_proc()):
        violations = vale.run("text")
    assert len(violations) == 1
    v = violations[0]
    assert (v.line, v.rule, v.severity) == (3, "vale:Google.Simply", "warning")


def test_run_maps_suggestion_to_warning():
    alert = dict(ALERT, Severity="suggestion")
    proc = _vale_proc(stdout=json.dumps({"f.md": [alert]}))
    with patch("guppi_committer.vale.subprocess.run", return_value=proc):
        assert vale.run("text")[0].severity == "warning"


def test_run_no_alerts():
    with patch("guppi_committer.vale.subprocess.run", return_value=_vale_proc(0, "{}")):
        assert vale.run("text") == []


def test_run_failure_raises():
    proc = _vale_proc(returncode=2, stdout="", stderr="bad config")
    with patch("guppi_committer.vale.subprocess.run", return_value=proc):
        with pytest.raises(RuntimeError, match="bad config"):
            vale.run("text")


# --- check integration ---


def test_check_auto_skips_without_vale():
    with patch("guppi_committer.vale.find_vale", return_value=None):
        result = runner.invoke(app, ["check"], input=GOOD)
    assert result.exit_code == 0


def test_check_auto_runs_when_configured(tmp_path):
    cfg = tmp_path / ".vale.ini"
    cfg.write_text("MinAlertLevel = suggestion\n")
    with (
        patch("guppi_committer.vale.find_vale", return_value="/usr/bin/vale"),
        patch("guppi_committer.vale.default_config", return_value=cfg),
        patch("guppi_committer.vale.run", return_value=[]) as mock_run,
    ):
        result = runner.invoke(app, ["check"], input=GOOD)
    assert result.exit_code == 0
    mock_run.assert_called_once()


def test_check_vale_alerts_are_warnings():
    from guppi_committer.checks import Violation

    alerts = [Violation(3, "vale:Google.Simply", "warning", "Remove 'simply'.")]
    with (
        patch("guppi_committer.vale.find_vale", return_value="/usr/bin/vale"),
        patch("guppi_committer.vale.run", return_value=alerts),
    ):
        assert runner.invoke(app, ["check", "--vale"], input=GOOD).exit_code == 0
        strict = runner.invoke(app, ["check", "--vale", "--strict"], input=GOOD)
    assert strict.exit_code == 1
    assert "vale:Google.Simply" in strict.output


def test_check_vale_forced_without_binary():
    with patch("guppi_committer.vale.find_vale", return_value=None):
        result = runner.invoke(app, ["check", "--vale"], input=GOOD)
    assert result.exit_code == 2


def test_check_no_vale_skips():
    with patch("guppi_committer.vale.run") as mock_run:
        result = runner.invoke(app, ["check", "--no-vale"], input=GOOD)
    assert result.exit_code == 0
    mock_run.assert_not_called()


# --- vale-setup ---


def test_vale_setup_writes_config(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    with patch("guppi_committer.vale.find_vale", return_value=None):
        result = runner.invoke(app, ["vale-setup"])
    assert result.exit_code == 0
    cfg_dir = tmp_path / "guppi" / "committer" / "vale"
    ini = (cfg_dir / ".vale.ini").read_text()
    assert "Packages = Google" in ini
    subs = (cfg_dir / "styles" / "STE" / "Substitutions.yml").read_text()
    assert "utilize: use" in subs
    filler = (cfg_dir / "styles" / "STE" / "Filler.yml").read_text()
    assert "- simply" in filler
    assert "brew install vale" in result.output


def test_vale_setup_syncs_when_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    ok = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with (
        patch("guppi_committer.vale.find_vale", return_value="/usr/bin/vale"),
        patch("guppi_committer.cli.subprocess.run", return_value=ok) as mock_run,
    ):
        result = runner.invoke(app, ["vale-setup"])
    assert result.exit_code == 0
    assert "Synced" in result.output
    assert mock_run.call_args.args[0][:2] == ["vale", "sync"]


def test_vale_setup_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    with patch("guppi_committer.vale.find_vale", return_value=None):
        assert runner.invoke(app, ["vale-setup"]).exit_code == 0
        assert runner.invoke(app, ["vale-setup"]).exit_code == 0
