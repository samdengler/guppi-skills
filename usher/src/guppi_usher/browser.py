"""Minimal Chrome bridge: run JavaScript in the active tab via AppleScript.

Data calls to regmovies.com sit behind Cloudflare and only succeed inside the
user's real, authenticated browser session — so usher executes its fetches in
the active Chrome tab rather than from a standalone HTTP client.

This is a self-contained bridge for now. It is slated to be replaced by the
`surfer` skill's `run` command once that is implemented (guppi-skills-j44).

Requirements (macOS):
    Chrome ▸ View ▸ Developer ▸ Allow JavaScript from Apple Events
"""

from __future__ import annotations

import subprocess


class BrowserError(RuntimeError):
    pass


def run_js(js: str, *, timeout: int = 30) -> str:
    """Execute ``js`` in Chrome's active tab and return the result as text.

    Raises BrowserError if Chrome is unavailable, Apple Events JS is disabled,
    or the script errors.
    """
    # Pass the JS to osascript via argv to avoid quoting/escaping pitfalls.
    script = (
        'on run argv\n'
        '  tell application "Google Chrome"\n'
        '    if (count of windows) is 0 then error "no Chrome window open"\n'
        '    set theTab to active tab of front window\n'
        '    set jsResult to (execute theTab javascript (item 1 of argv))\n'
        '    return jsResult as text\n'
        '  end tell\n'
        'end run'
    )
    try:
        proc = subprocess.run(
            ["osascript", "-e", script, js],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:  # pragma: no cover - platform guard
        raise BrowserError("osascript not found (usher's browser bridge needs macOS)") from exc
    except subprocess.TimeoutExpired as exc:
        raise BrowserError(f"Chrome JS timed out after {timeout}s") from exc

    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        if "Allow JavaScript from Apple Events" in stderr or "not allowed" in stderr.lower():
            raise BrowserError(
                "Chrome blocked JavaScript. Enable: "
                "View ▸ Developer ▸ Allow JavaScript from Apple Events"
            )
        raise BrowserError(stderr or "Chrome JavaScript execution failed")
    return proc.stdout.strip()


def fetch_json(url: str, *, timeout: int = 30) -> str:
    """Run a same-origin fetch from the active tab and return the response text.

    The active tab must already be on the target origin (e.g. regmovies.com) so
    the request carries the session's cookies and Cloudflare clearance.
    """
    js = (
        "(async () => {"
        f"  const r = await fetch({_js_str(url)}, {{headers:{{accept:'application/json'}}}});"
        "  return await r.text();"
        "})()"
    )
    return run_js(js, timeout=timeout)


def _js_str(value: str) -> str:
    """Encode a Python string as a JS string literal."""
    import json

    return json.dumps(value)
