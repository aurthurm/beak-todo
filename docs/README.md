# Documentation

| Document | Description |
|----------|-------------|
| [commands.md](commands.md) | CLI command reference (`t`, `t ai`, `t config`) |
| [beak-flow.md](beak-flow.md) | Beak Flow web UI — layout, dev workflow, drag-and-drop |
| [../ui/README.md](../ui/README.md) | **UI developers** — npm scripts, build output, Vite dev setup |
| [api.md](api.md) | REST API reference for Beak Flow (`/api/*`) |
| [architecture.md](architecture.md) | Project structure and data flow |
| [features.md](features.md) | Product overview and feature list |
| [integrations.md](integrations.md) | External integrations overview |
| [integrations/github.md](integrations/github.md) | GitHub sync setup and rules |
| [integrations/email.md](integrations/email.md) | Resend weekly reports (draft-first) |
| [channels/telegram.md](channels/telegram.md) | Telegram bot channel |

## Quick links

- **CLI only:** `pip install -e .` then `t init`
- **Beak Flow UI:** `beak-flow build-ui && beak-flow` (or Vite dev for UI hacking)
- **AI setup:** `t ai setup` and `t ai doctor`
- **Config file:** `~/.todos/config.toml` (`t config path`)
