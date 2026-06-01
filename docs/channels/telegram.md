# Telegram channel

Use Telegram as a lightweight mobile interface to the same todo engine as the CLI and Beak Flow.

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy the token.
2. Export the token:

```bash
export TELEGRAM_BOT_TOKEN="123456789:AAH..."
```

3. Initialize config:

```bash
t channels telegram setup
```

4. Start the bot (separate terminal from `beak-flow`):

```bash
t channels telegram run
```

5. DM your bot: `/start` — note your numeric **user id**.
6. Add that id to `~/.todos/config.toml`:

```toml
[telegram]
enabled = true
poll_timeout_seconds = 30
allowed_user_ids = [123456789]
confirm_email_send = true
confirm_github_sync = false
```

7. Verify:

```bash
t channels telegram doctor
```

## Security

Only Telegram user ids listed in `allowed_user_ids` can run commands (except `/start`, which shows your id). This is required because the app uses a single local SQLite database without login.

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Register channel account; show your user id |
| `/help` | Command list |
| `/today` | Tasks due today and overdue |
| `/add <text>` | Add task (AI parses priority/due) |
| `/done <id>` | Mark task complete |
| `/dump <text>` | Brain dump → preview → **Create** / **Cancel** |
| `/plan` | AI plan for today |
| `/report weekly` | Generate weekly email draft |
| `/email send` | Send current draft (**confirm** if `confirm_email_send`) |
| `/github` | List open issues/PRs in DB |
| `/github sync` | Run GitHub sync (optional confirm) |

## Confirmation rules

Actions that change external systems or create many todos require inline **Create/Send/Sync** or **Cancel** buttons:

- Brain dump batch create
- Email send via Resend
- GitHub sync (when `confirm_github_sync = true`)

Safe without confirmation: list tasks, add single task, mark done, generate report draft (send is separate).

## Architecture

```text
Telegram → src/channels/telegram/ → dispatcher → src/services/
```

Business logic stays in services; the Telegram package only parses messages and formats replies. See [architecture.md](../architecture.md).

## Production

- Run `t channels telegram run` under systemd or `tmux` alongside `beak-flow`.
- v1 uses **long polling** (`getUpdates`). Webhook mode may be added later for hosted deployments.
- Offset is stored in `~/.todos/telegram-offset.txt` so restarts do not replay old updates.

## Related

- [Email reports](../integrations/email.md) — weekly drafts sent after `/email send`
- [GitHub integration](../integrations/github.md) — sync before `/github` lists items
