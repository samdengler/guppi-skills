"""Telegram Bot API client using stdlib only."""

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

API_BASE = "https://api.telegram.org"


def _api_call(token: str, method: str, params: dict[str, Any] | None = None) -> dict:
    """Call a Telegram Bot API method and return the parsed response."""
    url = f"{API_BASE}/bot{token}/{method}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read())
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown')}")
    return data["result"]


def _post_json(token: str, method: str, payload: dict[str, Any]) -> dict:
    """POST JSON to a Telegram Bot API method."""
    url = f"{API_BASE}/bot{token}/{method}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown')}")
    return data["result"]


def _post_multipart(token: str, method: str, fields: dict[str, str], file_field: str, file_path: Path) -> dict:
    """POST multipart form data with a file to a Telegram Bot API method."""
    import uuid

    boundary = uuid.uuid4().hex
    lines: list[bytes] = []

    for key, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        lines.append(b"")
        lines.append(value.encode())

    lines.append(f"--{boundary}".encode())
    lines.append(f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"'.encode())
    lines.append(b"Content-Type: application/octet-stream")
    lines.append(b"")
    lines.append(file_path.read_bytes())
    lines.append(f"--{boundary}--".encode())

    body = b"\r\n".join(lines)
    url = f"{API_BASE}/bot{token}/{method}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data.get('description', 'unknown')}")
    return data["result"]


import urllib.parse  # noqa: E402 (grouped with urllib above)


def get_me(token: str) -> dict:
    """Verify bot token and return bot info (id, username, etc.)."""
    return _api_call(token, "getMe")


def get_updates(token: str, offset: int | None = None) -> list[dict]:
    """Fetch pending updates. Pass offset to acknowledge previous messages."""
    params: dict[str, Any] = {"timeout": 0}
    if offset is not None:
        params["offset"] = offset
    return _api_call(token, "getUpdates", params)


def get_file(token: str, file_id: str) -> dict:
    """Get file metadata including the download path."""
    return _api_call(token, "getFile", {"file_id": file_id})


def download_file(token: str, file_path: str, dest: Path) -> Path:
    """Download a file from Telegram to a local path."""
    url = f"{API_BASE}/file/bot{token}/{file_path}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:
        dest.write_bytes(resp.read())
    return dest


def send_message(token: str, chat_id: int, text: str) -> dict:
    """Send a text message to a chat."""
    return _post_json(token, "sendMessage", {"chat_id": chat_id, "text": text})


def send_document(token: str, chat_id: int, file_path: Path, caption: str | None = None) -> dict:
    """Send a file as a document to a chat."""
    fields: dict[str, str] = {"chat_id": str(chat_id)}
    if caption:
        fields["caption"] = caption
    return _post_multipart(token, "sendDocument", fields, "document", file_path)
