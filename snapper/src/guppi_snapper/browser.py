"""Chromium lifecycle management: find, launch, stop, state, CDP queries."""

import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from guppi_snapper.paths import state_file


def find_chromium_binary() -> Path | None:
    """Find Playwright's bundled Chromium binary. Returns None if not installed."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        path = Path(p.chromium.executable_path)
        if path.exists():
            return path
    return None


def install_chromium() -> bool:
    """Install Playwright's bundled Chromium. Returns True on success."""
    result = subprocess.run(
        ["playwright", "install", "chromium"],
        capture_output=False,
    )
    return result.returncode == 0


def is_port_in_use(port: int) -> bool:
    """Check if a TCP port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect(("localhost", port))
            return True
        except (ConnectionRefusedError, OSError):
            return False


def launch_chromium(
    chromium_path: Path,
    port: int,
    profile_dir: Path,
    extensions: list[Path] | None = None,
) -> int:
    """Launch Chromium with CDP enabled, detached from the current process.

    Returns the PID of the launched process.
    """
    args = [
        str(chromium_path),
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    if extensions:
        ext_paths = ",".join(str(e) for e in extensions)
        args.append(f"--load-extension={ext_paths}")
        args.append("--disable-extensions-except=" + ext_paths)

    process = subprocess.Popen(
        args,
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait briefly for the port to become available
    for _ in range(30):
        if is_port_in_use(port):
            break
        time.sleep(0.2)

    return process.pid


def save_state(pid: int, port: int, profile: str) -> None:
    """Save Chromium state to chromium.json."""
    sf = state_file()
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps({
        "pid": pid,
        "port": port,
        "profile": profile,
    }))


def load_state() -> dict | None:
    """Load Chromium state from chromium.json. Returns None if not found."""
    sf = state_file()
    if not sf.exists():
        return None
    try:
        return json.loads(sf.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def get_cdp_info(port: int) -> dict | None:
    """GET /json/version from the CDP endpoint. Returns parsed JSON or None."""
    try:
        with urlopen(f"http://localhost:{port}/json/version", timeout=3) as resp:
            return json.loads(resp.read())
    except (URLError, OSError, json.JSONDecodeError):
        return None


def list_tabs(port: int) -> list[dict]:
    """GET /json/list from the CDP endpoint. Returns list of tab info dicts."""
    try:
        with urlopen(f"http://localhost:{port}/json/list", timeout=3) as resp:
            return json.loads(resp.read())
    except (URLError, OSError, json.JSONDecodeError):
        return []


def stop_chromium(pid: int, sf: Path | None = None) -> None:
    """Stop a Chromium process by PID. SIGTERM, wait, SIGKILL if needed."""
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass  # Already dead

    # Wait up to 5 seconds for graceful shutdown
    for _ in range(50):
        try:
            os.kill(pid, 0)  # Check if still alive
            time.sleep(0.1)
        except ProcessLookupError:
            break
    else:
        # Force kill if still alive
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass

    # Clean up state file
    if sf is None:
        sf = state_file()
    if sf.exists():
        sf.unlink()
