"""Screenshot capture: viewport parsing, take_screenshot."""

import typer


def parse_viewport(viewport: str) -> tuple[int, int]:
    """Parse a 'WxH' viewport string into (width, height)."""
    parts = viewport.lower().split("x")
    if len(parts) != 2:
        typer.echo(f"Error: invalid viewport '{viewport}' (expected WxH, e.g. 1400x1092)", err=True)
        raise typer.Exit(1)
    try:
        width = int(parts[0])
        height = int(parts[1])
    except ValueError:
        typer.echo(f"Error: invalid viewport '{viewport}' (expected WxH, e.g. 1400x1092)", err=True)
        raise typer.Exit(1)
    return width, height


def take_screenshot(
    port: int,
    url: str,
    output: str,
    width: int,
    height: int,
    wait: int,
) -> None:
    """Connect to CDP, navigate to URL, and capture a screenshot.

    Uses browser.contexts[0] to reuse existing auth cookies/sessions.
    Disconnects without closing the browser.
    """
    from pathlib import Path

    from playwright.sync_api import sync_playwright

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://localhost:{port}")
        try:
            context = browser.contexts[0]
            page = context.new_page()
            page.set_viewport_size({"width": width, "height": height})
            page.goto(url, wait_until="load", timeout=60000)
            page.wait_for_timeout(wait * 1000)
            page.screenshot(path=str(output_path), type="png")
            page.close()
        finally:
            browser.close()
