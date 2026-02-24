"""GUPPI courier skill CLI"""

import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from guppi_courier import config
from guppi_courier import telegram

app = typer.Typer(help="Telegram-based messaging for Claude workflows")
console = Console()
err_console = Console(stderr=True)

# --- Domain commands ---


@app.command()
def pull(
    bot: Annotated[str | None, typer.Option("--bot", "-b", help="Bot name from registry")] = None,
    output: Annotated[str | None, typer.Option("--output", "-o", help="Directory for downloaded files")] = None,
    keep: Annotated[bool, typer.Option("--keep", help="Don't acknowledge messages")] = False,
):
    """Fetch the latest messages from a bot."""
    name, _ = config.get_bot(bot)
    token = config.get_token(name)
    offset = config.get_offset(name)

    updates = telegram.get_updates(token, offset=offset)
    if not updates:
        typer.echo("No new messages")
        return

    output_dir = Path(output) if output else Path.cwd()
    max_update_id = offset

    for update in updates:
        update_id = update["update_id"]
        if max_update_id is None or update_id >= max_update_id:
            max_update_id = update_id + 1

        msg = update.get("message", {})

        # Learn chat_id
        chat_id = msg.get("chat", {}).get("id")
        if chat_id:
            config.set_chat_id(name, chat_id)

        # Handle text
        text = msg.get("text")
        if text:
            typer.echo(text)

        # Handle documents
        doc = msg.get("document")
        if doc:
            file_info = telegram.get_file(token, doc["file_id"])
            file_name = doc.get("file_name", f"document_{update_id}")
            dest = output_dir / file_name
            telegram.download_file(token, file_info["file_path"], dest)
            err_console.print(f"Downloaded: {dest}")

        # Handle photos (highest resolution)
        photos = msg.get("photo")
        if photos:
            best = max(photos, key=lambda p: p.get("file_size", 0))
            file_info = telegram.get_file(token, best["file_id"])
            remote_path = file_info["file_path"]
            file_name = Path(remote_path).name
            dest = output_dir / file_name
            telegram.download_file(token, remote_path, dest)
            err_console.print(f"Downloaded: {dest}")

    if not keep and max_update_id is not None:
        config.set_offset(name, max_update_id)


@app.command()
def push(
    message: Annotated[str | None, typer.Argument(help="Text to send")] = None,
    bot: Annotated[str | None, typer.Option("--bot", "-b", help="Bot name from registry")] = None,
    file: Annotated[str | None, typer.Option("--file", "-f", help="File to send as document")] = None,
):
    """Send a message or file via the bot."""
    name, _ = config.get_bot(bot)
    token = config.get_token(name)
    chat_id = _resolve_chat_id(name, token)

    if file:
        file_path = Path(file)
        if not file_path.exists():
            err_console.print(f"File not found: {file_path}")
            raise typer.Exit(1)
        telegram.send_document(token, chat_id, file_path, caption=message)
        typer.echo(f"Sent: {file_path.name}")
    elif message:
        telegram.send_message(token, chat_id, message)
        typer.echo("Sent")
    else:
        # Read from stdin
        text = sys.stdin.read().strip()
        if not text:
            err_console.print("Nothing to send. Provide a message argument, --file, or pipe to stdin.")
            raise typer.Exit(1)
        telegram.send_message(token, chat_id, text)
        typer.echo("Sent")


@app.command()
def peek(
    bot: Annotated[str | None, typer.Option("--bot", "-b", help="Bot name from registry")] = None,
):
    """Preview waiting messages without acknowledging."""
    name, _ = config.get_bot(bot)
    token = config.get_token(name)
    offset = config.get_offset(name)

    updates = telegram.get_updates(token, offset=offset)
    if not updates:
        typer.echo("No new messages")
        return

    for update in updates:
        msg = update.get("message", {})
        text = msg.get("text")
        doc = msg.get("document")
        photos = msg.get("photo")

        if text:
            typer.echo(f"[text] {text}")
        if doc:
            typer.echo(f"[file] {doc.get('file_name', 'unnamed')}")
        if photos:
            typer.echo("[photo]")


@app.command()
def bots():
    """List registered bots and their status."""
    cfg = config.load_config()
    if not cfg["bots"]:
        typer.echo("No bots configured. Run: guppi-courier add <name>")
        return

    default_name = cfg.get("default")
    table = Table(show_header=True)
    table.add_column("Bot")
    table.add_column("Status")

    for name, bot_cfg in cfg["bots"].items():
        parts: list[str] = []
        has_tok = config.has_token(name)
        has_chat = config.get_chat_id(name) is not None

        if not has_tok:
            parts.append("token missing")
        elif not has_chat:
            bot_username = bot_cfg.get("name", name)
            parts.append(f"needs first message — open @{bot_username} in Telegram")
        else:
            parts.append("ready")

        if name == default_name:
            parts.append("(default)")

        table.add_row(name, " ".join(parts))

    console.print(table)


@app.command()
def add(
    name: Annotated[str, typer.Argument(help="Short name for the bot")],
    bot_name: Annotated[str | None, typer.Option("--bot-name", help="Telegram bot username")] = None,
    default: Annotated[bool, typer.Option("--default", help="Set as default bot")] = False,
):
    """Register a new bot."""
    # Check if re-running add for an existing bot (just re-check chat_id)
    cfg = config.load_config()
    existing = name in cfg.get("bots", {})

    if existing and config.has_token(name):
        token = config.get_token(name)
    else:
        token = typer.prompt("Token", hide_input=True)
        # Verify token
        try:
            me = telegram.get_me(token)
        except Exception as e:
            err_console.print(f"Invalid token: {e}")
            raise typer.Exit(1)
        username = me.get("username", "unknown")
        typer.echo(f"Verified: @{username}")

        # Store token and register bot
        config.set_token(name, token)
        if bot_name is None:
            bot_name = username
        config.add_bot(name, bot_name=bot_name, default=default)

    # Try to learn chat_id
    try:
        updates = telegram.get_updates(token)
        for update in updates:
            chat_id = update.get("message", {}).get("chat", {}).get("id")
            if chat_id:
                config.set_chat_id(name, chat_id)
                typer.echo("Chat ID learned — bot is ready")
                break
        else:
            resolved_name = bot_name or cfg.get("bots", {}).get(name, {}).get("name", name)
            typer.echo(
                f"No messages yet. Send a message to @{resolved_name} in Telegram, then run:\n"
                f"  guppi-courier add {name}"
            )
    except Exception:
        pass

    status = "default" if default or cfg.get("default") is None else ""
    needs_msg = " (needs first message)" if config.get_chat_id(name) is None else ""
    typer.echo(f"Bot '{name}' added{' (' + status + ')' if status else ''}{needs_msg}")


@app.command()
def remove(
    name: Annotated[str, typer.Argument(help="Bot name to remove")],
):
    """Remove a bot from the registry."""
    config.delete_token(name)
    config.remove_bot(name)
    typer.echo(f"Bot '{name}' removed")


# --- Helpers ---


def _resolve_chat_id(name: str, token: str) -> int:
    """Get chat_id for a bot, attempting to learn it if missing."""
    chat_id = config.get_chat_id(name)
    if chat_id is not None:
        return chat_id

    # Try to learn from pending updates
    updates = telegram.get_updates(token)
    for update in updates:
        cid = update.get("message", {}).get("chat", {}).get("id")
        if cid:
            config.set_chat_id(name, cid)
            return cid

    cfg = config.load_config()
    bot_username = cfg.get("bots", {}).get(name, {}).get("name", name)
    err_console.print(
        f"No chat ID for bot '{name}'. Send a message to @{bot_username} in Telegram first."
    )
    raise typer.Exit(1)


# --- Skill management subcommand group ---

skill_app = typer.Typer(help="Skill management commands")
app.add_typer(skill_app, name="skill")


@skill_app.command()
def install():
    """Register this skill with guppi-cli"""
    import subprocess

    skill_md = _get_skill_md_path()
    skill_dir = skill_md.parent
    result = subprocess.run(
        ["guppi", "skill", "install", "courier", "--from", str(skill_dir), "--yes"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        typer.echo(result.stdout.strip())
    else:
        typer.echo(f"Error: {result.stderr.strip()}", err=True)
        raise typer.Exit(1)


@skill_app.command()
def show():
    """Display SKILL.md contents"""
    skill_md = _get_skill_md_path()
    typer.echo(skill_md.read_text())


def _get_skill_md_path():
    """Locate SKILL.md bundled in the package"""
    package_dir = Path(__file__).parent
    skill_md = package_dir / "SKILL.md"
    if not skill_md.exists():
        # Fallback: look in the skill root (development mode)
        # package_dir = courier/src/guppi_courier → .parent.parent = courier/
        skill_md = package_dir.parent.parent / "SKILL.md"
    if not skill_md.exists():
        typer.echo("Error: SKILL.md not found", err=True)
        raise typer.Exit(1)
    return skill_md


if __name__ == "__main__":
    app()
