"""Tests for batch config loading and resolution."""

import pytest
import yaml
from typer import Exit

from guppi_snapper.batch import load_batch_config, resolve_capture


def _write_yaml(tmp_path, data):
    path = tmp_path / "config.yaml"
    path.write_text(yaml.dump(data))
    return path


def test_load_valid_config(tmp_path):
    config = {
        "viewport": "1400x1092",
        "wait": 8,
        "output_dir": "./screenshots",
        "captures": [
            {"url": "https://example.com", "output": "example.png"},
            {"url": "https://other.com", "output": "other.png", "wait": 3},
        ],
    }
    path = _write_yaml(tmp_path, config)
    result = load_batch_config(path)
    assert len(result["captures"]) == 2
    assert result["viewport"] == "1400x1092"


def test_load_missing_file(tmp_path):
    with pytest.raises((Exit, SystemExit)):
        load_batch_config(tmp_path / "nonexistent.yaml")


def test_load_missing_captures(tmp_path):
    path = _write_yaml(tmp_path, {"viewport": "1400x1092"})
    with pytest.raises((Exit, SystemExit)):
        load_batch_config(path)


def test_load_capture_missing_url(tmp_path):
    path = _write_yaml(tmp_path, {
        "captures": [{"output": "test.png"}],
    })
    with pytest.raises((Exit, SystemExit)):
        load_batch_config(path)


def test_load_capture_missing_output(tmp_path):
    path = _write_yaml(tmp_path, {
        "captures": [{"url": "https://example.com"}],
    })
    with pytest.raises((Exit, SystemExit)):
        load_batch_config(path)


def test_resolve_capture_uses_defaults():
    defaults = {"viewport": "1400x1365", "wait": 8, "output_dir": "./shots"}
    capture = {"url": "https://example.com", "output": "test.png"}
    result = resolve_capture(capture, defaults)
    assert result["viewport"] == "1400x1365"
    assert result["wait"] == 8
    assert result["output_dir"] == "./shots"
    assert result["url"] == "https://example.com"
    assert result["output"] == "test.png"


def test_resolve_capture_override():
    defaults = {"viewport": "1400x1365", "wait": 8, "output_dir": "."}
    capture = {
        "url": "https://example.com",
        "output": "test.png",
        "viewport": "800x600",
        "wait": 2,
    }
    result = resolve_capture(capture, defaults)
    assert result["viewport"] == "800x600"
    assert result["wait"] == 2


def test_resolve_capture_empty_defaults():
    capture = {"url": "https://example.com", "output": "test.png"}
    result = resolve_capture(capture, {})
    assert result["viewport"] == "1400x1365"
    assert result["wait"] == 5
    assert result["output_dir"] == "."
    assert result["existing"] is False
    assert result["resize"] is None


def test_resolve_capture_existing_flag():
    defaults = {"viewport": "1400x1365", "wait": 5}
    capture = {"url": "spreadsheets", "output": "sheet.png", "existing": True, "wait": 3}
    result = resolve_capture(capture, defaults)
    assert result["existing"] is True
    assert result["wait"] == 3


def test_resolve_capture_resize_from_defaults():
    defaults = {"viewport": "1400x1365", "resize": "1120x1092"}
    capture = {"url": "https://example.com", "output": "test.png"}
    result = resolve_capture(capture, defaults)
    assert result["resize"] == "1120x1092"


def test_resolve_capture_resize_null_override():
    """Setting resize to None in a capture disables the global default."""
    defaults = {"viewport": "1400x1365", "resize": "1120x1092"}
    capture = {"url": "https://example.com", "output": "test.png", "resize": None}
    result = resolve_capture(capture, defaults)
    assert result["resize"] is None


def test_resolve_capture_resize_per_capture():
    defaults = {"viewport": "1400x1365", "resize": "1120x1092"}
    capture = {"url": "https://example.com", "output": "test.png", "resize": "800x600"}
    result = resolve_capture(capture, defaults)
    assert result["resize"] == "800x600"


def test_load_invalid_yaml(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(": : : invalid yaml [[[")
    with pytest.raises((Exit, SystemExit)):
        load_batch_config(path)
