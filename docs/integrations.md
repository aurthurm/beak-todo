# Integrations

Beak Todo can link local planning tasks to work in external systems and send **weekly work reports** by email.

| Channel | Provider | Doc |
|---------|----------|-----|
| Input / sync | GitHub (issues & PRs) | [github.md](integrations/github.md) |
| Output | Resend (email) | [email.md](integrations/email.md) |
| Chat I/O | Telegram (bot) | [../channels/telegram.md](../channels/telegram.md) |

## Design

| Layer | Purpose |
|-------|---------|
| **Source** | Where work comes from: `GitHub → organisation → repository` |
| **Planning** | Due date, priority, calendar position, done (local only) |
| **Tags** | Flexible context: `bug`, `lims`, `urgent` (not org/repo names) |

Display example:

```text
[GitHub] [beak-insights/beak-lims] #1025
Fix worksheet printing issue
Tags: lims, bug, support
```

## Configuration

| Path | Purpose |
|------|---------|
| `~/.todos/integrations/github.toml` | Repos to sync, token env name |
| `GITHUB_TOKEN` | Personal access token (recommended) |

## CLI

```bash
t integrations github setup
t integrations github doctor
t integrations github repos add beak-insights/beak-lims
t integrations github sync
t integrations github link 42 https://github.com/org/repo/issues/1
t integrations github unlink 42
t tag list
t tag add 42 bug urgent
```

## API

See [api.md](api.md) — `/api/integrations/github/*`, todo `source` / `tag` filters, `/api/tags`.

## Adding another provider

1. Create `src/integrations/<provider>/` with `client`, `sync`, `integration.py`
2. Register in `src/integrations/registry.py`
3. Add `external_sources.provider` value and CLI group under `t integrations`

See [integrations/github.md](integrations/github.md) for GitHub-specific sync rules.

## Email (Resend)

Weekly reports: todos + GitHub + notes → draft → user approval → send.

```bash
t email doctor
t email draft weekly
t email send-draft
```

See [integrations/email.md](integrations/email.md).

## Telegram

Mobile chat interface: `/today`, `/add`, `/dump`, `/report weekly`, etc.

```bash
export TELEGRAM_BOT_TOKEN="..."
t channels telegram setup
t channels telegram run
```

See [channels/telegram.md](../channels/telegram.md).
