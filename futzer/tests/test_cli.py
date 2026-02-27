"""Tests for guppi-futzer."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from guppi_futzer.cli import app
from guppi_futzer.config import resolve_profile
from guppi_futzer.modules.zsh import generate

runner = CliRunner()


# --- ZSH module tests ---


class TestZshGenerate:
    def test_generates_all_sections(self):
        output = generate()
        assert "# --- Completion ---" in output
        assert "# --- History ---" in output
        assert "# --- Options ---" in output
        assert "# --- Vi Mode ---" in output
        assert "# --- Keybindings ---" in output
        assert "# --- Prompt ---" in output

    def test_includes_matcher_list(self):
        output = generate()
        assert "matcher-list" in output
        assert "l:|=* r:|=*" in output

    def test_includes_vi_mode(self):
        output = generate()
        assert "bindkey -v" in output
        assert "KEYTIMEOUT=1" in output

    def test_includes_compinit(self):
        output = generate()
        assert "autoload -Uz compinit && compinit" in output

    def test_terminal_in_header(self):
        output = generate(terminal="ghostty")
        assert "# Terminal: ghostty" in output

        output = generate(terminal="iterm2")
        assert "# Terminal: iterm2" in output

    def test_includes_vcs_info_prompt(self):
        output = generate()
        assert "vcs_info" in output
        assert "PROMPT=" in output


# --- Config/profile tests ---


class TestProfile:
    def test_default_profile(self, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text("[default]\n")
        profile = resolve_profile("default", config)
        assert profile.name == "default"
        assert profile.terminal == "ghostty"

    def test_named_profile_overrides(self, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text('[default]\n\n[work]\nterminal = "iterm2"\n')
        profile = resolve_profile("work", config)
        assert profile.name == "work"
        assert profile.terminal == "iterm2"

    def test_inherits_from_default(self, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text('[default]\nterminal = "iterm2"\n\n[work]\n')
        profile = resolve_profile("work", config)
        assert profile.terminal == "iterm2"

    def test_named_profile_overrides_default(self, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text('[default]\nterminal = "ghostty"\n\n[work]\nterminal = "iterm2"\n')
        profile = resolve_profile("work", config)
        assert profile.terminal == "iterm2"

    def test_missing_config_uses_defaults(self, tmp_path):
        config = tmp_path / "nonexistent.toml"
        profile = resolve_profile("default", config)
        assert profile.terminal == "ghostty"

    def test_env_var_profile(self, tmp_path, monkeypatch):
        config = tmp_path / "config.toml"
        config.write_text('[default]\n\n[work]\nterminal = "iterm2"\n')
        monkeypatch.setenv("FUTZER_PROFILE", "work")
        profile = resolve_profile(config_path=config)
        assert profile.name == "work"
        assert profile.terminal == "iterm2"


# --- CLI tests ---


class TestGenerateCommand:
    def test_generate_zsh_stdout(self):
        result = runner.invoke(app, ["generate", "zsh"])
        assert result.exit_code == 0
        assert "# --- Completion ---" in result.output

    def test_generate_zsh_to_file(self, tmp_path):
        out = tmp_path / "zsh.zsh"
        result = runner.invoke(app, ["generate", "zsh", "-o", str(out)])
        assert result.exit_code == 0
        assert out.exists()
        content = out.read_text()
        assert "matcher-list" in content

    def test_generate_zsh_with_profile(self, tmp_path):
        config = tmp_path / "config.toml"
        config.write_text('[work]\nterminal = "iterm2"\n')
        # Profile flag works but reads from default config location;
        # just verify the flag is accepted
        result = runner.invoke(app, ["generate", "zsh", "--profile", "work"])
        assert result.exit_code == 0


class TestStatusCommand:
    def test_status_runs(self):
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Profile:" in result.output
