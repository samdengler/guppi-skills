"""Tests for guppi-clipper CLI."""

from unittest.mock import patch, MagicMock

from typer.testing import CliRunner

from guppi_clipper.cli import app

runner = CliRunner()


def test_copy_from_file(tmp_path):
    """Copy content from a file to clipboard."""
    f = tmp_path / "input.txt"
    f.write_text("hello clipboard")

    with patch("guppi_clipper.cli._copy_to_clipboard") as mock_copy:
        result = runner.invoke(app, ["copy", "--file", str(f)])

    assert result.exit_code == 0
    mock_copy.assert_called_once_with("hello clipboard")
    assert "15 bytes" in result.output
    assert "hello clipboard" in result.output


def test_copy_from_stdin():
    """Copy content from stdin to clipboard."""
    with patch("guppi_clipper.cli._copy_to_clipboard") as mock_copy:
        result = runner.invoke(app, ["copy"], input="piped content")

    assert result.exit_code == 0
    mock_copy.assert_called_once_with("piped content")
    assert "Copied" in result.output


def test_copy_file_not_found():
    """Error when file doesn't exist."""
    result = runner.invoke(app, ["copy", "--file", "/nonexistent/file.txt"])
    assert result.exit_code == 1


def test_copy_empty_content(tmp_path):
    """Warning when content is empty."""
    f = tmp_path / "empty.txt"
    f.write_text("")

    result = runner.invoke(app, ["copy", "--file", str(f)])
    assert result.exit_code == 0
    assert "Empty content" in result.output


def test_copy_saves_temp_file(tmp_path):
    """Copy saves content to a temp file."""
    f = tmp_path / "input.txt"
    f.write_text("save me")

    with patch("guppi_clipper.cli._copy_to_clipboard"):
        result = runner.invoke(app, ["copy", "--file", str(f)])

    assert result.exit_code == 0
    assert "/tmp/clipper-" in result.output


def test_copy_preview_truncates(tmp_path):
    """Preview is truncated to ~80 chars."""
    f = tmp_path / "long.txt"
    f.write_text("x" * 200)

    with patch("guppi_clipper.cli._copy_to_clipboard"):
        result = runner.invoke(app, ["copy", "--file", str(f)])

    assert result.exit_code == 0
    # Preview line should be shorter than the full content
    for line in result.output.split("\n"):
        if line.startswith("Preview:"):
            # 80 chars of x's + the "Preview: " prefix + quotes
            assert len(line) < 120


def test_copy_multiline_preview(tmp_path):
    """Multiline content has newlines collapsed in preview."""
    f = tmp_path / "multi.txt"
    f.write_text("line one\nline two\nline three")

    with patch("guppi_clipper.cli._copy_to_clipboard"):
        result = runner.invoke(app, ["copy", "--file", str(f)])

    assert result.exit_code == 0
    for line in result.output.split("\n"):
        if line.startswith("Preview:"):
            assert "line one line two" in line


def test_paste():
    """Paste prints clipboard contents."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "clipboard content"

    with patch("guppi_clipper.cli.subprocess.run", return_value=mock_result):
        result = runner.invoke(app, ["paste"])

    assert result.exit_code == 0
    assert "clipboard content" in result.output


def test_paste_error():
    """Paste handles clipboard command failure."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "not available"

    with patch("guppi_clipper.cli.subprocess.run", return_value=mock_result):
        result = runner.invoke(app, ["paste"])

    assert result.exit_code == 1


def test_get_clipboard_commands_macos():
    """Detects macOS clipboard commands."""
    with patch("guppi_clipper.cli.sys") as mock_sys:
        mock_sys.platform = "darwin"
        from guppi_clipper.cli import _get_clipboard_commands
        copy_cmd, paste_cmd = _get_clipboard_commands()
    assert copy_cmd == ["pbcopy"]
    assert paste_cmd == ["pbpaste"]


def test_skill_show():
    """Skill show prints SKILL.md."""
    result = runner.invoke(app, ["skill", "show"])
    assert result.exit_code == 0
    assert "clipper" in result.output
    assert "guppi-clipper" in result.output
