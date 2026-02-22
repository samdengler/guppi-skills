"""YAML batch config loading and resolution."""

from pathlib import Path

import typer
import yaml


def load_batch_config(path: Path) -> dict:
    """Parse a YAML batch config file.

    Expected format:
        viewport: 1400x1365
        resize: 1120x1092
        wait: 8
        output_dir: ./screenshots
        captures:
          - url: https://example.com
            output: example.png
          - url: spreadsheets
            existing: true
            output: sheet.png
            wait: 3
          - url: http://localhost:8888/admin
            output: admin.png
            viewport: 1120x1092
            resize: null
    """
    if not path.exists():
        typer.echo(f"Error: config file not found: {path}", err=True)
        raise typer.Exit(1)

    try:
        data = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        typer.echo(f"Error: invalid YAML: {e}", err=True)
        raise typer.Exit(1)

    if not isinstance(data, dict):
        typer.echo("Error: config must be a YAML mapping", err=True)
        raise typer.Exit(1)

    if "captures" not in data or not isinstance(data["captures"], list):
        typer.echo("Error: config must contain a 'captures' list", err=True)
        raise typer.Exit(1)

    for i, cap in enumerate(data["captures"]):
        if "url" not in cap:
            typer.echo(f"Error: capture {i} missing 'url'", err=True)
            raise typer.Exit(1)
        if "output" not in cap:
            typer.echo(f"Error: capture {i} missing 'output'", err=True)
            raise typer.Exit(1)

    return data


def resolve_capture(capture: dict, defaults: dict) -> dict:
    """Merge a single capture entry with global defaults.

    Per-capture values override defaults for viewport, wait, output_dir,
    existing, and resize. Setting resize to null in a capture disables
    the global resize default for that entry.
    """
    # resize: None means "not set", explicit null in YAML disables global default
    resize = capture.get("resize", defaults.get("resize"))

    return {
        "url": capture["url"],
        "output": capture["output"],
        "viewport": capture.get("viewport", defaults.get("viewport", "1400x1365")),
        "wait": capture.get("wait", defaults.get("wait", 5)),
        "output_dir": capture.get("output_dir", defaults.get("output_dir", ".")),
        "existing": capture.get("existing", defaults.get("existing", False)),
        "resize": resize,
    }
