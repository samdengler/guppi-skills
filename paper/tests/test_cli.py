"""Tests for guppi-paper CLI."""

from typer.testing import CliRunner

from guppi_paper.cli import app

runner = CliRunner()


def test_prompt_outputs_hydrated_template():
    url = "https://arxiv.org/pdf/2509.07604"
    result = runner.invoke(app, ["prompt", url])
    assert result.exit_code == 0
    assert url in result.output
    assert "<paper_analysis>" in result.output
    assert "<paper_url>" in result.output
    assert "Feynman Technique" in result.output


def test_prompt_substitutes_url():
    url = "https://example.com/paper.pdf"
    result = runner.invoke(app, ["prompt", url])
    assert result.exit_code == 0
    assert url in result.output
    assert "INSERT_YOUR_PAPER_URL_HERE" not in result.output


def test_pdf_missing_file(tmp_path):
    missing = tmp_path / "nonexistent.md"
    result = runner.invoke(app, ["pdf", str(missing)])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_skill_show():
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "paper" in result.output
    assert "guppi-paper" in result.output
