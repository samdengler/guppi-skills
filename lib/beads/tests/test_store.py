"""Tests for BeadsStore."""

import json
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from guppi_beads import BeadsStore


@pytest.fixture
def store(tmp_path):
    """A BeadsStore with data_dir pointed at a temp directory."""
    s = BeadsStore("testskill", prefix="tst")
    with patch.object(type(s), "data_dir", new_callable=lambda: property(lambda self: tmp_path)):
        yield s


# -- available() -------------------------------------------------------------


def test_available_when_bd_installed(store):
    with patch("guppi_beads.store.shutil.which", return_value="/usr/bin/bd"):
        assert store.available() is True


def test_available_when_bd_missing(store):
    with patch("guppi_beads.store.shutil.which", return_value=None):
        assert store.available() is False


# -- initialized -------------------------------------------------------------


def test_initialized_false_when_no_db(store):
    assert store.initialized is False


def test_initialized_true_when_db_exists(store):
    db_dir = store.data_dir / ".beads"
    db_dir.mkdir(parents=True)
    (db_dir / "beads.db").touch()
    assert store.initialized is True


# -- ensure() ----------------------------------------------------------------


def test_ensure_returns_false_when_bd_missing(store):
    with patch.object(store, "available", return_value=False):
        assert store.ensure() is False


def test_ensure_noops_when_already_initialized(store):
    db_dir = store.data_dir / ".beads"
    db_dir.mkdir(parents=True)
    (db_dir / "beads.db").touch()

    with patch.object(store, "available", return_value=True), \
         patch.object(store, "run") as mock_run:
        assert store.ensure() is True
        mock_run.assert_not_called()


def test_ensure_calls_bd_init(store):
    result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    with patch.object(store, "available", return_value=True), \
         patch.object(store, "run", return_value=result) as mock_run:
        assert store.ensure() is True
        mock_run.assert_called_once_with(
            ["init", "--skip-hooks", "--skip-merge-driver", "--prefix", "tst"]
        )


def test_ensure_creates_data_dir(store):
    """ensure() creates the data directory before calling bd init."""
    result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    with patch.object(store, "available", return_value=True), \
         patch.object(store, "run", return_value=result):
        store.ensure()
        assert store.data_dir.exists()


def test_ensure_without_prefix(tmp_path):
    """ensure() omits --prefix when none is configured."""
    s = BeadsStore("nopfx")
    result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    with patch.object(type(s), "data_dir", new_callable=lambda: property(lambda self: tmp_path)), \
         patch.object(s, "available", return_value=True), \
         patch.object(s, "run", return_value=result) as mock_run:
        s.ensure()
        mock_run.assert_called_once_with(
            ["init", "--skip-hooks", "--skip-merge-driver"]
        )


# -- run() -------------------------------------------------------------------


def test_run_passes_args_and_cwd(store):
    result = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result) as mock_run:
        out = store.run(["list", "--json"])
        mock_run.assert_called_once_with(
            ["bd", "list", "--json"],
            cwd=store.data_dir,
            capture_output=True,
            text=True,
        )
        assert out.stdout == "ok"


def test_run_returns_failure_when_bd_missing(store):
    with patch.object(store, "available", return_value=False):
        result = store.run(["list"])
        assert result.returncode == 1
        assert "not found" in result.stderr


# -- find_by_title() ---------------------------------------------------------


def test_find_by_title_exact_match(store):
    issues = [
        {"id": "tst-1", "title": "Alpha"},
        {"id": "tst-2", "title": "Beta"},
    ]
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(issues), stderr=""
    )

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result):
        found = store.find_by_title("Beta")
        assert found is not None
        assert found["id"] == "tst-2"


def test_find_by_title_no_match(store):
    issues = [{"id": "tst-1", "title": "Alpha"}]
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(issues), stderr=""
    )

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result):
        assert store.find_by_title("Gamma") is None


def test_find_by_title_no_partial_match(store):
    """find_by_title uses exact match, not substring."""
    issues = [{"id": "tst-1", "title": "Alpha Beta"}]
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(issues), stderr=""
    )

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result):
        assert store.find_by_title("Alpha") is None


# -- list_issues() -----------------------------------------------------------


def test_list_issues_default(store):
    issues = [{"id": "tst-1", "title": "Task"}]
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout=json.dumps(issues), stderr=""
    )

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result) as mock_run:
        out = store.list_issues()
        assert len(out) == 1
        # Verify --all and --status are NOT passed
        call_args = mock_run.call_args[0][0]
        assert "--all" not in call_args
        assert "--status" not in call_args


def test_list_issues_with_status(store):
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="[]", stderr=""
    )

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result) as mock_run:
        store.list_issues(status="open")
        call_args = mock_run.call_args[0][0]
        assert "--status" in call_args
        assert "open" in call_args


def test_list_issues_with_all(store):
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="[]", stderr=""
    )

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result) as mock_run:
        store.list_issues(all=True)
        call_args = mock_run.call_args[0][0]
        assert "--all" in call_args


def test_list_issues_returns_empty_on_failure(store):
    with patch.object(store, "available", return_value=False):
        assert store.list_issues() == []


def test_list_issues_returns_empty_on_bad_json(store):
    result = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="not json", stderr=""
    )

    with patch.object(store, "available", return_value=True), \
         patch("guppi_beads.store.subprocess.run", return_value=result):
        assert store.list_issues() == []
