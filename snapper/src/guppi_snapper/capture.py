"""Screenshot capture: viewport parsing, take_screenshot, resize."""

import subprocess

import typer

DEFAULT_VIEWPORT = "1400x1365"


def parse_viewport(viewport: str) -> tuple[int, int]:
    """Parse a 'WxH' viewport string into (width, height)."""
    parts = viewport.lower().split("x")
    if len(parts) != 2:
        typer.echo(f"Error: invalid viewport '{viewport}' (expected WxH, e.g. 1400x1365)", err=True)
        raise typer.Exit(1)
    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError:
        typer.echo(f"Error: invalid viewport '{viewport}' (expected WxH, e.g. 1400x1365)", err=True)
        raise typer.Exit(1)
    return width, height


def resize_image(input_path: str, width: int, height: int) -> None:
    """Resize an image proportionally using ImageMagick.

    Uses `magick` (ImageMagick 7). The resize is proportional — both dimensions
    must share the same aspect ratio as the source.
    """
    result = subprocess.run(
        ["magick", input_path, "-resize", f"{width}x{height}", input_path],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        typer.echo(f"Error: resize failed: {result.stderr.strip()}", err=True)
        typer.echo("Is ImageMagick installed? (brew install imagemagick)", err=True)
        raise typer.Exit(1)


def find_existing_page(context, url_pattern: str):
    """Find an existing tab whose URL contains the given pattern."""
    for page in context.pages:
        if url_pattern in page.url:
            return page
    return None


def take_screenshot(
    port: int,
    url: str,
    output: str,
    width: int,
    height: int,
    wait: int,
    existing: bool = False,
    resize: tuple[int, int] | None = None,
) -> None:
    """Connect to CDP and capture a screenshot.

    If existing=True, finds an already-open tab matching the URL pattern
    instead of navigating a new page. This preserves cell selection, scroll
    position, and UI state — essential for canvas-based apps like Google Sheets.

    If resize is set, proportionally resize the captured image after screenshot.
    """
    from pathlib import Path

    from playwright.sync_api import sync_playwright

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
        try:
            context = browser.contexts[0]

            if existing:
                page = find_existing_page(context, url)
                if not page:
                    typer.echo(f"Error: no open tab matching '{url}'", err=True)
                    raise typer.Exit(1)
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(wait * 1000)
                page.screenshot(path=str(output_path), type="png")
            else:
                page = context.new_page()
                page.set_viewport_size({"width": width, "height": height})
                page.goto(url, wait_until="load", timeout=60000)
                page.wait_for_timeout(wait * 1000)
                page.screenshot(path=str(output_path), type="png")
                page.close()
        finally:
            browser.close()

    if resize:
        resize_image(str(output_path), resize[0], resize[1])
