"""Tests for guppi-dotfiles CLI."""

import json
import subprocess
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from guppi_dotfiles.cli import app

runner = CliRunner()

BREWFILE = """\
# CLI tools
brew "gh"
brew "postgresql@16"
brew "steveyegge/beads/bd"

cask "ghostty"
cask "claude-code@latest"
"""

MISE_CONFIG = """\
[tools]
node = "24"
bat = "latest"
"npm:netlify-cli" = "latest"
"""


@pytest.fixture
def dotfiles(tmp_path, monkeypatch):
    """A fake dotfiles repo, mise global config, and XDG config dir."""
    root = tmp_path / "dotfiles"
    root.mkdir()
    (root / "Brewfile").write_text(BREWFILE)
    mise_dir = root / "mise"
    mise_dir.mkdir()
    mise_config = mise_dir / "config.toml"
    mise_config.write_text(MISE_CONFIG)
    xdg = tmp_path / "xdg"
    xdg.mkdir()
    monkeypatch.setenv("DOTFILES_PATH", str(root))
    monkeypatch.setenv("MISE_GLOBAL_CONFIG_FILE", str(mise_config))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(xdg))
    return root


class FakeRunner:
    """Replaces _run. Records commands and answers from a table keyed by command prefix."""

    def __init__(self, responses: dict[tuple[str, ...], str | tuple[int, str]] | None = None):
        self.responses = responses or {}
        self.calls: list[list[str]] = []

    def __call__(self, cmd, check=True, capture=True):
        self.calls.append(cmd)
        for prefix, response in self.responses.items():
            if tuple(cmd[: len(prefix)]) == prefix:
                if isinstance(response, tuple):
                    code, out = response
                else:
                    code, out = 0, response
                return subprocess.CompletedProcess(args=cmd, returncode=code, stdout=out, stderr="")
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    def commands(self) -> list[str]:
        return [" ".join(cmd) for cmd in self.calls]


@pytest.fixture
def fake_run():
    runner_obj = FakeRunner()
    with patch("guppi_dotfiles.cli._run", runner_obj), patch("guppi_dotfiles.cli.shutil.which", return_value="/bin/x"):
        yield runner_obj


# --- version / list ---


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.startswith("guppi-dotfiles ")


def test_list_json_reads_both_manifests(dotfiles):
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    rows = json.loads(result.stdout)
    assert {"name": "node", "via": "mise"} in rows
    assert {"name": "npm:netlify-cli", "via": "mise"} in rows
    assert {"name": "steveyegge/beads/bd", "via": "brew"} in rows
    assert {"name": "claude-code@latest", "via": "cask"} in rows
    assert not any(row["name"] == "CLI tools" for row in rows)


def test_list_without_manifests_is_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("DOTFILES_PATH", str(tmp_path / "nope"))
    monkeypatch.setenv("MISE_GLOBAL_CONFIG_FILE", str(tmp_path / "nope.toml"))
    result = runner.invoke(app, ["list", "--json"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == []


# --- add ---


def test_add_prefixed_spec_goes_to_mise_without_lookup(dotfiles, fake_run):
    result = runner.invoke(app, ["add", "pipx:httpie"])
    assert result.exit_code == 0, result.stdout
    assert fake_run.commands() == ["mise use --global --yes pipx:httpie"]


def test_add_prefers_mise_when_registry_knows_it(dotfiles, fake_run):
    fake_run.responses[("mise", "registry", "jq")] = "aqua:jqlang/jq"
    result = runner.invoke(app, ["add", "jq"])
    assert result.exit_code == 0, result.stdout
    assert "mise use --global --yes jq" in fake_run.commands()
    assert not any(cmd.startswith("brew") for cmd in fake_run.commands())


def test_add_version_spec_routes_on_tool_name(dotfiles, fake_run):
    fake_run.responses[("mise", "registry", "go")] = "core:go"
    result = runner.invoke(app, ["add", "go@1.23"])
    assert result.exit_code == 0, result.stdout
    assert "mise registry go" in fake_run.commands()
    assert "mise use --global --yes go@1.23" in fake_run.commands()


def test_add_falls_back_to_brew_formula(dotfiles, fake_run):
    fake_run.responses[("mise", "registry", "colima")] = (1, "")
    fake_run.responses[("brew", "info")] = json.dumps({"formulae": [{"name": "colima"}], "casks": []})
    result = runner.invoke(app, ["add", "colima"])
    assert result.exit_code == 0, result.stdout
    cmds = fake_run.commands()
    assert "brew install colima" in cmds
    assert f"brew bundle add --file {dotfiles / 'Brewfile'} colima" in cmds


def test_add_falls_back_to_cask(dotfiles, fake_run):
    fake_run.responses[("mise", "registry", "rectangle-pro")] = (1, "")
    fake_run.responses[("brew", "info")] = json.dumps({"formulae": [], "casks": [{"token": "rectangle-pro"}]})
    result = runner.invoke(app, ["add", "rectangle-pro"])
    assert result.exit_code == 0, result.stdout
    cmds = fake_run.commands()
    assert "brew install --cask rectangle-pro" in cmds
    assert f"brew bundle add --file {dotfiles / 'Brewfile'} --cask rectangle-pro" in cmds


def test_add_via_overrides_routing(dotfiles, fake_run):
    result = runner.invoke(app, ["add", "jq", "--via", "brew"])
    assert result.exit_code == 0, result.stdout
    cmds = fake_run.commands()
    assert not any(cmd.startswith("mise registry") for cmd in cmds)
    assert "brew install jq" in cmds


def test_add_unknown_package_fails(dotfiles, fake_run):
    fake_run.responses[("mise", "registry")] = (1, "")
    fake_run.responses[("brew", "info")] = (1, "")
    result = runner.invoke(app, ["add", "nosuchthing"])
    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_add_skips_packages_already_in_manifest(dotfiles, fake_run):
    result = runner.invoke(app, ["add", "gh", "node", "ghostty"])
    assert result.exit_code == 0, result.stdout
    assert fake_run.calls == []
    assert result.stdout.count("Skipped") == 3


# --- remove ---


def test_remove_mise_entry(dotfiles, fake_run):
    result = runner.invoke(app, ["remove", "bat"])
    assert result.exit_code == 0, result.stdout
    assert fake_run.commands() == ["mise unuse --global bat"]


def test_remove_mise_entry_keep(dotfiles, fake_run):
    result = runner.invoke(app, ["remove", "bat", "--keep"])
    assert result.exit_code == 0, result.stdout
    assert fake_run.commands() == ["mise unuse --global bat --no-prune"]


def test_remove_brew_formula(dotfiles, fake_run):
    result = runner.invoke(app, ["remove", "gh"])
    assert result.exit_code == 0, result.stdout
    assert fake_run.commands() == [
        f"brew bundle remove --file {dotfiles / 'Brewfile'} --formula gh",
        "brew uninstall --formula gh",
    ]


def test_remove_cask_keep(dotfiles, fake_run):
    result = runner.invoke(app, ["remove", "ghostty", "--keep"])
    assert result.exit_code == 0, result.stdout
    assert fake_run.commands() == [f"brew bundle remove --file {dotfiles / 'Brewfile'} --cask ghostty"]


def test_remove_unknown_is_skipped(dotfiles, fake_run):
    result = runner.invoke(app, ["remove", "nothing"])
    assert result.exit_code == 0
    assert "Skipped" in result.stdout
    assert fake_run.calls == []


# --- drift ---


def _drift_responses(fake_run):
    fake_run.responses[("brew", "leaves")] = "gh\nbd\nrestatedev/tap/restate\nyt-dlp\n"
    fake_run.responses[("brew", "list", "--formula")] = "gh\nbd\nrestate\nyt-dlp\n"
    fake_run.responses[("brew", "list", "--cask")] = "ghostty\ncalibre\n"
    fake_run.responses[("mise", "ls", "--json", "--installed")] = json.dumps({
        "node": [{"installed": True, "source": {"type": "mise.toml", "path": "x"}}],
        "bat": [{"installed": True, "source": {"type": "mise.toml", "path": "x"}}],
        "stray": [{"installed": True}],
        "projectonly": [{"installed": True, "source": {"type": "mise.toml", "path": "/proj/mise.toml"}}],
    })
    fake_run.responses[("mise", "ls", "--json", "--missing")] = json.dumps({"npm:netlify-cli": []})


def test_drift_json(dotfiles, fake_run):
    _drift_responses(fake_run)
    result = runner.invoke(app, ["drift", "--json"])
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["extra"] == [
        {"name": "restatedev/tap/restate", "via": "brew"},
        {"name": "yt-dlp", "via": "brew"},
        {"name": "calibre", "via": "cask"},
        {"name": "stray", "via": "mise"},
    ]
    assert data["missing"] == [
        {"name": "postgresql@16", "via": "brew"},
        {"name": "claude-code@latest", "via": "cask"},
        {"name": "npm:netlify-cli", "via": "mise"},
    ]


def test_drift_respects_ignore_list(dotfiles, fake_run):
    _drift_responses(fake_run)
    runner.invoke(app, ["ignore", "yt-dlp", "calibre"])
    result = runner.invoke(app, ["drift", "--json"])
    data = json.loads(result.stdout)
    names = [item["name"] for item in data["extra"]]
    assert "yt-dlp" not in names
    assert "calibre" not in names
    assert "stray" in names


def test_drift_no_drift_message(dotfiles, fake_run):
    fake_run.responses[("brew", "leaves")] = "gh\npostgresql@16\nbd\n"
    fake_run.responses[("brew", "list", "--formula")] = "gh\npostgresql@16\nbd\n"
    fake_run.responses[("brew", "list", "--cask")] = "ghostty\nclaude-code@latest\n"
    fake_run.responses[("mise", "ls", "--json", "--installed")] = "{}"
    fake_run.responses[("mise", "ls", "--json", "--missing")] = "{}"
    result = runner.invoke(app, ["drift"])
    assert result.exit_code == 0
    assert "No drift" in result.stdout


def test_drift_fix_dry_run_plans_rehoming_to_mise(dotfiles, fake_run):
    _drift_responses(fake_run)
    fake_run.responses[("mise", "registry", "yt-dlp")] = "pipx:yt-dlp"
    fake_run.responses[("mise", "registry", "restate")] = (1, "")
    fake_run.responses[("mise", "registry", "calibre")] = (1, "")
    fake_run.responses[("mise", "registry", "stray")] = "ubi:stray"
    fake_run.responses[("brew", "info", "--json=v2", "restatedev/tap/restate")] = json.dumps(
        {"formulae": [{"name": "restate"}], "casks": []}
    )
    fake_run.responses[("brew", "info", "--json=v2", "calibre")] = json.dumps(
        {"formulae": [], "casks": [{"token": "calibre"}]}
    )
    result = runner.invoke(app, ["drift", "--fix", "--dry-run", "--json"])
    assert result.exit_code == 0, result.stdout
    data = json.loads(result.stdout)
    assert data["plan"] == [
        {"name": "restatedev/tap/restate", "from": "brew", "to": "brew"},
        {"name": "yt-dlp", "from": "brew", "to": "mise"},
        {"name": "calibre", "from": "cask", "to": "cask"},
        {"name": "stray", "from": "mise", "to": "mise"},
    ]
    assert not any(cmd.startswith(("mise use", "brew install", "brew bundle")) for cmd in fake_run.commands())


def test_drift_fix_installs_and_syncs(dotfiles, fake_run):
    _drift_responses(fake_run)
    fake_run.responses[("mise", "registry")] = (1, "")
    fake_run.responses[("brew", "info")] = json.dumps({"formulae": [{"name": "x"}], "casks": []})
    result = runner.invoke(app, ["drift", "--fix", "--via", "brew"])
    assert result.exit_code == 0, result.stdout
    cmds = fake_run.commands()
    assert "brew install yt-dlp" in cmds
    assert f"brew bundle add --file {dotfiles / 'Brewfile'} yt-dlp" in cmds
    assert "brew install calibre" in cmds
    assert f"brew bundle install --file {dotfiles / 'Brewfile'} --no-upgrade" in cmds
    assert "mise install --yes" in cmds
    assert "calibre is now managed by brew" in result.stdout


# --- sync / ignore ---


def test_sync(dotfiles, fake_run):
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    assert fake_run.commands() == [
        f"brew bundle install --file {dotfiles / 'Brewfile'} --no-upgrade",
        "mise install --yes",
    ]


def test_ignore_add_list_remove(dotfiles):
    assert runner.invoke(app, ["ignore", "--json"]).stdout.strip() == "[]"
    runner.invoke(app, ["ignore", "b", "a"])
    assert json.loads(runner.invoke(app, ["ignore", "--json"]).stdout) == ["a", "b"]
    runner.invoke(app, ["ignore", "--remove", "a"])
    assert json.loads(runner.invoke(app, ["ignore", "--json"]).stdout) == ["b"]
    config = json.loads((dotfiles.parent / "xdg" / "guppi" / "dotfiles" / "config.json").read_text())
    assert config["ignore"] == ["b"]


# --- skill ---


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "name: dotfiles" in result.stdout
