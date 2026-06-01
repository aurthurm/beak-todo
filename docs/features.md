# Features Overview

Felicity Todos is a local-first task manager with a terminal CLI, optional AI, and the **Beak Flow** web planning gateway.

## Implemented

### Task management (CLI + API + UI)

- Add, edit, delete todos
- Priorities 0–3 with color coding
- Categories (create, rename, delete, filter)
- Due dates and overdue detection
- Completion status
- Notes per task
- Keyword search
- CSV export/import
- Statistics (`t stats`)
- Within-day `sort_order` (UI/API)

### Terminal CLI (`t`)

- Short mnemonic commands (`t a`, `t l`, `t e`, …)
- Rich table and colored list views
- Auto-create database on first command (`ensure_db`)

### AI (CLI + API)

- Natural language task creation (`t ai add`)
- Brain dump batch parse (UI + `/api/ai/brain-dump`)
- Daily planning (`t ai plan`, UI **AI Plan**)
- Summary, risks, smart search, breakdown, chat
- Dual-mode providers: LiteLLM (default) + opt-in Codex/Claude harness
- Config file: `~/.todos/config.toml`
- `t ai setup`, `t ai doctor`, `t config`

### Beak Flow (web UI)

- Three-panel desktop layout: brain dump, calendar strip, day view
- Drag-and-drop: inbox ↔ days ↔ done
- AI Organise with preview and selective add
- AI drawer with preview/apply for mutations
- Task detail modal with notes
- Mobile tab layout
- Shares `~/.todos/todos.db` with CLI

## Planned / not in v1

- Interactive CLI mode (`t interactive`) — mentioned in early PRD only
- Subtasks / `parent_id`
- Recurring tasks
- Multi-user / auth
- Push notifications
- External calendar sync
- PostgreSQL backend

## User personas

| Persona | Primary tool |
|---------|----------------|
| Power user | `t` CLI, scripting, quick capture |
| Planner | Beak Flow UI, calendar drag, brain dump |
| Both | Same data; CLI for speed, UI for planning |

## Documentation map

| Doc | Content |
|-----|---------|
| [README.md](README.md) | Doc index |
| [commands.md](commands.md) | CLI reference |
| [beak-flow.md](beak-flow.md) | Web UI guide |
| [api.md](api.md) | REST API |
| [architecture.md](architecture.md) | Code and schema |
