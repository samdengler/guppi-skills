"""Tests for guppi-tracker CLI."""

import contextlib
import json
import subprocess
from unittest.mock import patch, PropertyMock

from typer.testing import CliRunner

from guppi_beads import BeadsStore
from guppi_tracker.cli import app, _store

runner = CliRunner()


# --- Helpers ---


def _mock_store_unavailable():
    """Patch store so bd is not on PATH."""
    return patch.object(_store, "available", return_value=False)


@contextlib.contextmanager
def _mock_store(issues=None):
    """Patch store to be available with optional issues.

    Yields a list that collects args from each store.run() call.
    """
    issues = issues or []
    run_calls: list[list[str]] = []

    def _mock_run(args):
        run_calls.append(args)
        if args[0] == "create":
            return subprocess.CompletedProcess(
                args=[], returncode=0,
                stdout="Created trk-abc\n  Title: test", stderr=""
            )
        if args[0] == "list":
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout=json.dumps(issues), stderr=""
            )
        if args[0] == "search":
            query = args[1].lower() if len(args) > 1 else ""
            matches = [
                i for i in issues
                if query in i.get("title", "").lower() or query in i.get("description", "").lower()
            ]
            if matches:
                lines = [f"{m['id']}: {m['title']}" for m in matches]
                return subprocess.CompletedProcess(
                    args=[], returncode=0, stdout="\n".join(lines), stderr=""
                )
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
        if args[0] == "show":
            issue_id = args[1] if len(args) > 1 else ""
            match = next((i for i in issues if i["id"] == issue_id), None)
            if match:
                return subprocess.CompletedProcess(
                    args=[], returncode=0,
                    stdout=f"ID: {match['id']}\nTitle: {match['title']}", stderr=""
                )
            return subprocess.CompletedProcess(
                args=[], returncode=1, stdout="", stderr=f"issue not found: {issue_id}"
            )
        if args[0] in ("update", "close"):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    with patch.object(_store, "available", return_value=True), \
         patch.object(_store, "ensure", return_value=True), \
         patch.object(BeadsStore, "initialized", new_callable=PropertyMock, return_value=True), \
         patch.object(_store, "run", side_effect=_mock_run):
        yield run_calls


# --- version ---


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "guppi-tracker" in result.output


# --- add ---


def test_add_basic():
    with _mock_store() as run_calls:
        result = runner.invoke(app, ["add", "Read DDIA chapter 5"])
        assert result.exit_code == 0
        create_calls = [c for c in run_calls if c[0] == "create"]
        assert len(create_calls) == 1
        assert "Read DDIA chapter 5" in create_calls[0]


def test_add_with_tags():
    with _mock_store() as run_calls:
        result = runner.invoke(app, ["add", "Read DDIA", "--tag", "toread", "--tag", "books"])
        assert result.exit_code == 0
        create_calls = [c for c in run_calls if c[0] == "create"]
        assert "--labels" in create_calls[0]
        assert "toread,books" in create_calls[0]


def test_add_with_note():
    with _mock_store() as run_calls:
        result = runner.invoke(app, ["add", "Try Plasmo", "--note", "Chrome extension framework"])
        assert result.exit_code == 0
        create_calls = [c for c in run_calls if c[0] == "create"]
        assert "--description" in create_calls[0]
        assert "Chrome extension framework" in create_calls[0]


def test_add_fails_without_bd():
    with _mock_store_unavailable():
        result = runner.invoke(app, ["add", "test"])
        assert result.exit_code == 1
        assert "bd CLI not found" in result.output


# --- list ---


def test_list_empty():
    with _mock_store():
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "No items found" in result.output


def test_list_shows_items():
    issues = [
        {"id": "trk-abc", "title": "Read DDIA", "labels": ["toread"], "status": "open"},
        {"id": "trk-def", "title": "Try Plasmo", "labels": ["idea"], "status": "open"},
    ]
    with _mock_store(issues):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "Read DDIA" in result.output
        assert "Try Plasmo" in result.output
        assert "toread" in result.output
        assert "idea" in result.output
        assert "trk-abc" in result.output


def test_list_with_tag_filter():
    with _mock_store() as run_calls:
        runner.invoke(app, ["list", "--tag", "toread"])
        list_calls = [c for c in run_calls if c[0] == "list"]
        assert "--label" in list_calls[0]
        assert "toread" in list_calls[0]


def test_list_with_all():
    with _mock_store() as run_calls:
        runner.invoke(app, ["list", "--all"])
        list_calls = [c for c in run_calls if c[0] == "list"]
        assert "--all" in list_calls[0]


# --- done ---


def test_done():
    with _mock_store() as run_calls:
        result = runner.invoke(app, ["done", "trk-abc"])
        assert result.exit_code == 0
        assert "Done: trk-abc" in result.output
        close_calls = [c for c in run_calls if c[0] == "close"]
        assert len(close_calls) == 1
        assert "trk-abc" in close_calls[0]


# --- tag ---


def test_tag_adds_labels():
    with _mock_store() as run_calls:
        result = runner.invoke(app, ["tag", "trk-abc", "backend", "caching"])
        assert result.exit_code == 0
        assert "Tagged trk-abc" in result.output
        assert "backend, caching" in result.output
        update_calls = [c for c in run_calls if c[0] == "update"]
        assert len(update_calls) == 2


# --- show ---


def test_show():
    issues = [{"id": "trk-abc", "title": "Read DDIA", "labels": [], "status": "open"}]
    with _mock_store(issues):
        result = runner.invoke(app, ["show", "trk-abc"])
        assert result.exit_code == 0
        assert "Read DDIA" in result.output


def test_show_not_found():
    with _mock_store():
        result = runner.invoke(app, ["show", "trk-zzz"])
        assert result.exit_code == 1


# --- search ---


def test_search_matches():
    issues = [{"id": "trk-abc", "title": "Read DDIA chapter 5", "description": "", "labels": []}]
    with _mock_store(issues):
        result = runner.invoke(app, ["search", "DDIA"])
        assert result.exit_code == 0
        assert "DDIA" in result.output


def test_search_no_match():
    with _mock_store():
        result = runner.invoke(app, ["search", "nonexistent"])
        assert result.exit_code == 1
        assert "No items matching" in result.output


# --- skill ---


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "tracker" in result.output
