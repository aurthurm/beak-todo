"""CLI: t channels telegram ..."""

from __future__ import annotations

import logging

import typer

from src.channels.telegram.bot import run_polling
from src.channels.telegram.client import TelegramClient
from src.channels.telegram.config import get_bot_token
from src.config import ensure_default_config, get_telegram_config, save_config

channels_app = typer.Typer(help="Messaging channels (Telegram, …)")
telegram_app = typer.Typer(help="Telegram bot")
channels_app.add_typer(telegram_app, name="telegram")


@telegram_app.command("setup")
def telegram_setup():
    """Print BotFather steps and enable telegram in config."""
    ensure_default_config()
    save_config(
        {
            "telegram": {
                "enabled": True,
                "poll_timeout_seconds": 30,
                "allowed_user_ids": [],
                "confirm_email_send": True,
                "confirm_github_sync": False,
            }
        }
    )
    typer.echo("Telegram section added to ~/.todos/config.toml")
    typer.echo("")
    typer.echo("1. Message @BotFather on Telegram → /newbot → copy token")
    typer.echo("2. export TELEGRAM_BOT_TOKEN='your-token'")
    typer.echo("3. Run: t channels telegram run")
    typer.echo("4. DM your bot with /start — note your user id")
    typer.echo("5. Add your id to [telegram].allowed_user_ids in config.toml")


@telegram_app.command("doctor")
def telegram_doctor():
    """Verify token, API, and allowlist."""
    token = get_bot_token()
    if not token:
        typer.echo("TELEGRAM_BOT_TOKEN is not set")
        raise typer.Exit(1)
    typer.echo("TELEGRAM_BOT_TOKEN is set")

    cfg = get_telegram_config()
    typer.echo(f"enabled: {cfg.enabled}")
    typer.echo(f"poll_timeout_seconds: {cfg.poll_timeout_seconds}")
    if cfg.allowed_user_ids:
        typer.echo(f"allowed_user_ids: {cfg.allowed_user_ids}")
    else:
        typer.echo("allowed_user_ids: (empty — only /start works until configured)")

    try:
        client = TelegramClient()
        me = client.get_me()
        typer.echo(f"Bot: @{me.get('username')} (id={me.get('id')})")
    except Exception as exc:
        typer.echo(f"getMe failed: {exc}")
        raise typer.Exit(1)
    typer.echo("Telegram looks OK.")


@telegram_app.command("run")
def telegram_run(
    once: bool = typer.Option(False, "--once", help="Process one poll batch and exit"),
):
    """Run long-polling bot (blocking)."""
    logging.basicConfig(level=logging.INFO)
    if not get_bot_token():
        typer.echo("Set TELEGRAM_BOT_TOKEN first.")
        raise typer.Exit(1)
    typer.echo("Starting Telegram bot (Ctrl+C to stop)...")
    try:
        run_polling(once=once)
    except KeyboardInterrupt:
        typer.echo("\nStopped.")
