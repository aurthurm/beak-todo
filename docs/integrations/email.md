# Email (Resend)

Beak Todo can send **weekly work reports** by email using [Resend](https://resend.com). Reports are built from local todos, notes, and linked GitHub items, then sent only after you approve a draft.

## Setup

1. Create a Resend account and verify your sending domain.
2. Create an API key and export it:

```bash
export RESEND_API_KEY=re_xxxxxxxx
```

3. Configure `~/.todos/config.toml`:

```toml
[email]
provider = "resend"
from = "Your Name <updates@yourdomain.com>"
default_to = "boss@company.com"
send_mode = "draft_first"
```

4. Verify configuration:

```bash
t email doctor
```

## Draft-first workflow

With `send_mode = "draft_first"` (default), the app never sends email until you explicitly approve:

1. Generate a draft: `t email draft weekly` or `t report weekly --save`
2. Review: `t email show-draft`
3. Send: `t email send-draft` (or use the **Reports** tab in Beak Flow)

Use `--force` only when you intentionally bypass draft checks for one-off sends.

## Commands

| Command | Description |
|---------|-------------|
| `t report weekly` | Print weekly report (last 7 days) |
| `t report weekly --no-ai` | Deterministic bullet list |
| `t report weekly --save` | Save as email draft |
| `t email doctor` | Check API key and config |
| `t email draft weekly` | Generate and save draft |
| `t email show-draft` | Show current draft |
| `t email send-draft [--to addr]` | Send approved draft |
| `t email history` | Recent sends |
| `t ai email "…"` | Preview AI edits (does not send) |

## Report content

Section toggles live under `[reports.weekly]` in `config.toml`:

- Completed tasks (`completed_at` in range)
- GitHub issues/PRs updated in range
- Blockers (tag `blocked` or high-priority overdue)
- Notes added in range
- Upcoming priorities (open todos)

## Scheduling (cron)

The app does not auto-send in v1. Example Friday afternoon workflow:

```cron
30 15 * * 5 cd /path/to/beak-todo && t integrations github sync && t email draft weekly
```

Review the draft, then run `t email send-draft` when ready.

## Beak Flow API

- `POST /api/reports/weekly/generate`
- `GET /api/reports/draft`
- `POST /api/reports/draft/send`
- `DELETE /api/reports/draft`
- `GET /api/email/status`

See [API reference](../api.md).
