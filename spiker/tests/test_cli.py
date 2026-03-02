"""Tests for guppi-spiker CLI."""

import contextlib
import json
import re
import subprocess
from unittest.mock import patch, MagicMock, PropertyMock

from typer.testing import CliRunner

from guppi_beads import BeadsStore
from guppi_spiker.cli import app, _store

runner = CliRunner()


# --- Helpers ---


def _mock_store_unavailable():
    """Patch store to be unavailable (bd not installed)."""
    return patch.object(_store, "available", return_value=False)


@contextlib.contextmanager
def _mock_store_available(issues=None):
    """Patch store to be available with optional issues.

    Yields a list that collects (command, args) tuples from store.run calls.
    """
    issues = issues or []
    run_calls: list[list[str]] = []

    def _mock_run(args):
        run_calls.append(args)
        if args[0] == "create":
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
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
            return subprocess.CompletedProcess(
                args=[], returncode=0, stdout=json.dumps(matches), stderr=""
            )
        if args[0] in ("update", "close"):
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    with patch.object(_store, "available", return_value=True), \
         patch.object(_store, "ensure", return_value=True), \
         patch.object(BeadsStore, "initialized", new_callable=PropertyMock, return_value=True), \
         patch.object(_store, "run", side_effect=_mock_run), \
         patch.object(_store, "find_by_title", side_effect=lambda t: next((i for i in issues if i["title"] == t), None)), \
         patch.object(_store, "list_issues", return_value=issues):
        yield run_calls


# --- new ---


def test_new_with_name(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result = runner.invoke(app, ["new", "my-spike", "--no-git"])
    assert result.exit_code == 0
    path = result.output.strip()
    assert "my-spike" in path
    assert re.match(r".*\d{4}-\d{2}-\d{2}-my-spike$", path)


def test_new_without_name(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result = runner.invoke(app, ["new", "--no-git"])
    assert result.exit_code == 0
    path = result.output.strip()
    assert re.match(r".*\d{4}-\d{2}-\d{2}-\w+-\w+-\w+$", path)


def test_new_creates_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result = runner.invoke(app, ["new", "test-spike", "--no-git"])
    from pathlib import Path
    assert Path(result.output.strip()).is_dir()


def test_new_with_git(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result = runner.invoke(app, ["new", "git-spike"])
    from pathlib import Path
    spike_path = Path(result.output.strip())
    assert (spike_path / ".git").is_dir()


def test_new_creates_agents_md(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result = runner.invoke(app, ["new", "agent-spike", "--no-git"])
    from pathlib import Path
    spike_path = Path(result.output.strip())
    agents_md = spike_path / "AGENTS.md"
    assert agents_md.exists()
    content = agents_md.read_text()
    assert "agent-spike" in content
    assert "guppi-spiker describe" in content
    assert "guppi-spiker tag" in content
    assert "guppi-spiker done" in content


def test_new_with_summary_creates_beads_issue(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_available() as run_calls:
        result = runner.invoke(app, ["new", "redis-test", "--no-git", "--summary", "Testing pub/sub"])
        assert result.exit_code == 0
        create_calls = [c for c in run_calls if c[0] == "create"]
        assert len(create_calls) == 1
        assert "--description" in create_calls[0]
        assert "Testing pub/sub" in create_calls[0]


def test_new_without_summary_creates_beads_issue(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_available() as run_calls:
        result = runner.invoke(app, ["new", "plain-spike", "--no-git"])
        assert result.exit_code == 0
        create_calls = [c for c in run_calls if c[0] == "create"]
        assert len(create_calls) == 1
        assert "--description" not in create_calls[0]


def test_new_idempotent_same_name(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result1 = runner.invoke(app, ["new", "my-spike", "--no-git"])
        result2 = runner.invoke(app, ["new", "my-spike", "--no-git"])
    assert result1.exit_code == 0
    assert result2.exit_code == 0
    assert result1.output.strip() == result2.output.strip()


def test_new_idempotent_different_day(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2025-01-15-old-spike").mkdir()
    with _mock_store_unavailable():
        result = runner.invoke(app, ["new", "old-spike", "--no-git"])
    assert result.exit_code == 0
    assert result.output.strip().endswith("2025-01-15-old-spike")


def test_new_idempotent_no_extra_dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        runner.invoke(app, ["new", "only-one", "--no-git"])
        runner.invoke(app, ["new", "only-one", "--no-git"])
        runner.invoke(app, ["new", "only-one", "--no-git"])
    dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
    assert len(dirs) == 1


def test_new_random_name_not_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result1 = runner.invoke(app, ["new", "--no-git"])
        result2 = runner.invoke(app, ["new", "--no-git"])
    assert result1.exit_code == 0
    assert result2.exit_code == 0
    dirs = [d for d in tmp_path.iterdir() if d.is_dir()]
    assert len(dirs) >= 1


# --- list ---


def test_list_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "No spikes found" in result.output


def test_list_shows_spikes(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-10-alpha").mkdir()
    (tmp_path / "2026-02-12-beta").mkdir()
    with _mock_store_unavailable():
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "beta" in result.output
    assert "alpha" in result.output


def test_list_shows_summary_from_beads(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-test").mkdir()
    issues = [{"id": "spike-1", "title": "2026-02-12-redis-test", "description": "Testing pub/sub", "status": "open"}]
    with _mock_store_available(issues):
        result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "redis-test" in result.output
    assert "Testing pub/sub" in result.output


def test_list_hides_closed_by_default(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-10-done-spike").mkdir()
    (tmp_path / "2026-02-12-active-spike").mkdir()
    issues = [
        {"id": "spike-1", "title": "2026-02-10-done-spike", "description": "", "status": "closed"},
        {"id": "spike-2", "title": "2026-02-12-active-spike", "description": "", "status": "open"},
    ]
    with _mock_store_available(issues):
        result = runner.invoke(app, ["list"])
    assert "active-spike" in result.output
    assert "done-spike" not in result.output


def test_list_all_includes_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-10-done-spike").mkdir()
    (tmp_path / "2026-02-12-active-spike").mkdir()
    issues = [
        {"id": "spike-1", "title": "2026-02-10-done-spike", "description": "", "status": "closed"},
        {"id": "spike-2", "title": "2026-02-12-active-spike", "description": "", "status": "open"},
    ]
    with _mock_store_available(issues):
        result = runner.invoke(app, ["list", "--all"])
    assert "active-spike" in result.output
    assert "done-spike" in result.output


def test_list_filter_by_status(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-10-parked").mkdir()
    (tmp_path / "2026-02-12-active").mkdir()
    issues = [
        {"id": "spike-1", "title": "2026-02-10-parked", "description": "", "status": "deferred"},
        {"id": "spike-2", "title": "2026-02-12-active", "description": "", "status": "open"},
    ]
    with _mock_store_available(issues):
        result = runner.invoke(app, ["list", "--status", "deferred"])
    assert "parked" in result.output
    assert "active" not in result.output


# --- find ---


def test_find_matches(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-caching").mkdir()
    (tmp_path / "2026-02-12-graphql-test").mkdir()
    with _mock_store_unavailable():
        result = runner.invoke(app, ["find", "redis"])
    assert result.exit_code == 0
    assert "redis-caching" in result.output


def test_find_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-caching").mkdir()
    with _mock_store_unavailable():
        result = runner.invoke(app, ["find", "nonexistent"])
    assert result.exit_code == 1


def test_find_case_insensitive(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-Redis-Caching").mkdir()
    with _mock_store_unavailable():
        result = runner.invoke(app, ["find", "redis"])
    assert result.exit_code == 0
    assert "Redis-Caching" in result.output


def test_find_searches_beads_metadata(tmp_path, monkeypatch):
    """Find matches on beads description even when slug doesn't match."""
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-fuzzy-teal-otter").mkdir()
    issues = [{"id": "spike-1", "title": "2026-02-12-fuzzy-teal-otter", "description": "Redis pub/sub test"}]
    with _mock_store_available(issues):
        result = runner.invoke(app, ["find", "redis"])
    assert result.exit_code == 0
    assert "fuzzy-teal-otter" in result.output


# --- path ---


def test_path_returns_first_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-10-redis-old").mkdir()
    (tmp_path / "2026-02-12-redis-new").mkdir()
    result = runner.invoke(app, ["path", "redis"])
    assert result.exit_code == 0
    assert "redis-new" in result.output
    assert result.output.strip().count("\n") == 0


def test_path_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["path", "nonexistent"])
    assert result.exit_code == 1


# --- describe ---


def test_describe_updates_summary(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-test").mkdir()
    issues = [{"id": "spike-1", "title": "2026-02-12-redis-test", "description": "", "status": "open"}]
    with _mock_store_available(issues) as run_calls:
        result = runner.invoke(app, ["describe", "redis", "Testing pub/sub"])
        assert result.exit_code == 0
        assert "Updated summary" in result.output
        update_calls = [c for c in run_calls if c[0] == "update"]
        assert len(update_calls) == 1
        assert "--description" in update_calls[0]
        assert "Testing pub/sub" in update_calls[0]


def test_describe_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    with _mock_store_unavailable():
        result = runner.invoke(app, ["describe", "nonexistent", "summary"])
    assert result.exit_code == 1


def test_describe_no_beads(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-test").mkdir()
    with _mock_store_unavailable(), \
         patch.object(_store, "ensure", return_value=False):
        result = runner.invoke(app, ["describe", "redis", "summary"])
    assert result.exit_code == 1
    assert "Beads not available" in result.output


# --- tag ---


def test_tag_adds_labels(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-test").mkdir()
    issues = [{"id": "spike-1", "title": "2026-02-12-redis-test", "description": "", "status": "open"}]
    with _mock_store_available(issues) as run_calls:
        result = runner.invoke(app, ["tag", "redis", "backend", "caching"])
        assert result.exit_code == 0
        assert "Tagged" in result.output
        assert "backend, caching" in result.output
        update_calls = [c for c in run_calls if c[0] == "update"]
        assert len(update_calls) == 2  # one per tag


def test_tag_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["tag", "nonexistent", "foo"])
    assert result.exit_code == 1


# --- park ---


def test_park_sets_deferred(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-test").mkdir()
    issues = [{"id": "spike-1", "title": "2026-02-12-redis-test", "description": "", "status": "open"}]
    with _mock_store_available(issues) as run_calls:
        result = runner.invoke(app, ["park", "redis"])
        assert result.exit_code == 0
        assert "Parked" in result.output
        update_calls = [c for c in run_calls if c[0] == "update"]
        assert len(update_calls) == 1
        assert "deferred" in update_calls[0]


def test_park_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["park", "nonexistent"])
    assert result.exit_code == 1


# --- done ---


def test_done_closes_issue(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    (tmp_path / "2026-02-12-redis-test").mkdir()
    issues = [{"id": "spike-1", "title": "2026-02-12-redis-test", "description": "", "status": "open"}]
    with _mock_store_available(issues) as run_calls:
        result = runner.invoke(app, ["done", "redis"])
        assert result.exit_code == 0
        assert "Done" in result.output
        close_calls = [c for c in run_calls if c[0] == "close"]
        assert len(close_calls) == 1


def test_done_no_match(tmp_path, monkeypatch):
    monkeypatch.setenv("SPIKER_PATH", str(tmp_path))
    result = runner.invoke(app, ["done", "nonexistent"])
    assert result.exit_code == 1


# --- skill ---


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "spiker" in result.output
    assert "guppi-spiker" in result.output
