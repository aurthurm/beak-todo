# Beak Flow — Planning Gateway

Beak Flow turns Felicity Todos into a **lightweight planning gateway**: messy thoughts → AI-structured tasks → drag into a simple calendar → focus on today.

The terminal CLI (`t`) remains the power-user layer. The UI is for faster capture, visual planning, and rescheduling.

## Product idea

> A lightweight AI planning gateway where messy thoughts become structured tasks, then tasks are dragged into a simple calendar flow.

**Not in v1:** auth, teams, notifications, recurring tasks, Google Calendar sync, PostgreSQL.

## Architecture

```text
~/.todos/todos.db
       ↓
src/services/   (todos, notes, categories, ai_service)
       ↓
t CLI  +  FastAPI (/api)  +  Vue UI (ui/)
```

See [architecture.md](architecture.md) for schema and module layout. See [api.md](api.md) for REST details.

## Installation and run

### Prerequisites

- Python 3.10+
- Node.js 18+ (only for `beak-flow build-ui` or Vite dev mode)

### Production (single port — recommended)

```bash
pip install -e .
beak-flow build-ui
beak-flow
```

Open http://127.0.0.1:8787 — API and UI on one process. Static files live in `src/api/static/` inside the Python package (included in wheels when pre-built).

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8787/ | Beak Flow UI |
| http://127.0.0.1:8787/docs | OpenAPI |

### Background service (start at login)

```bash
beak-flow build-ui              # required once before first use
beak-flow install-service       # writes OS service + starts now
beak-flow service-status
```

| OS | Mechanism | Unit location |
|----|-----------|---------------|
| Linux | systemd user service | `~/.config/systemd/user/beak-flow.service` |
| macOS | launchd | `~/Library/LaunchAgents/com.beak.flow.plist` |
| Windows | Task Scheduler | Task name `BeakFlow` |

Server settings persist in `~/.todos/beak-flow.toml` (host, port, log path). Override with `BEAK_FLOW_HOST`, `BEAK_FLOW_PORT`, or `BEAK_FLOW_LOG`.

**Linux:** run `loginctl enable-linger $USER` if you want Beak Flow to keep running after you log out.

```bash
beak-flow uninstall-service
```

### UI development (hot reload)

```bash
beak-flow                        # Terminal 1 — API
cd ui && npm install && npm run dev   # Terminal 2 — UI :5173
```

Vite proxies `/api` → `8787`.

### AI setup

Brain dump and the AI drawer need a provider:

```bash
export OPENAI_API_KEY="..."
t ai doctor          # verify resolution
```

Or configure in `~/.todos/config.toml` (see [commands.md](commands.md)).

### GitHub work in the UI

Use the **Sources** sidebar to filter local vs GitHub tasks by organisation and repository, and filter by **tags**. Click **Sync GitHub** after configuring [integrations/github.md](integrations/github.md).

## UI layout

### Desktop (three columns)

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Beak Flow    [Search...]              Today | This Week | AI Plan | AI  │
├──────────────┬────────────────────────────────────┬─────────────────────┤
│ Brain Dump   │  ← Mon │ Tue │ Wed │ Thu │ Fri →   │ Selected day        │
│ + Inbox      │  draggable cards per column        │ Overdue / priority  │
│              │  + Done drop zone                  │ / Done buckets      │
└──────────────┴────────────────────────────────────┴─────────────────────┘
│ AI drawer (bottom)                                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

| Panel | Features |
|-------|----------|
| **Left** | Free-text brain dump, **AI Organise**, checkbox review, **Add Selected**, inbox list |
| **Middle** | Horizontal calendar strip (14 days), drag between inbox / days / done |
| **Right** | Day view for selected date: Overdue, Critical/High/Medium/Low, Done |
| **Drawer** | Preset prompts, chat, action preview with Apply/Cancel |
| **Modal** | Task details: edit fields, notes |

### Mobile (< 900px)

Tab bar: **Inbox | Calendar | Today | AI** — one panel at a time. Same API.

## Key workflows

### 1. Brain dump

1. Type messy thoughts in the left panel.  
2. Click **AI Organise**.  
3. Review suggested tasks (category, priority, due date).  
4. Uncheck any you do not want.  
5. Click **Add Selected** → tasks saved to SQLite (inbox or with due dates).

### 2. Calendar planning

- Drag a card from **Inbox** onto a day → sets `due_date`.  
- Drag between days → updates `due_date`.  
- Drag to **Done** → `completed: true`.  
- Drag back to **Inbox** → clears due date.

### 3. Day focus

- Click a day in the calendar → right panel shows that date.  
- Tasks grouped: Overdue (if any), then by priority, then Done.

### 4. AI assistant

- **AI Plan** (top bar) — suggested focus for today.  
- **AI** button — drawer with presets, e.g. “Move low-priority to next week”.  
- Mutating suggestions show a **preview** list; click **Apply** to commit.

## Task cards

- Soft white cards, minimal border.  
- **Priority stripe** on the left (matches CLI colors: blue / yellow / orange / red).  
- Subtitle: category and due hint.

## Tech stack

| Layer | Stack |
|-------|--------|
| Backend | FastAPI, Pydantic, existing services + AI layer |
| Frontend | Vue 3, TypeScript, Vite, Pinia, vue-draggable-plus |
| Data | SQLite at `~/.todos/todos.db` |
| AI | LiteLLM (same as CLI) |

## UI project structure

Source lives under [`ui/`](../ui/). See **[ui/README.md](../ui/README.md)** for npm scripts, dev vs production build, and file layout.

```text
ui/src/          → Vue components, Pinia store, api/client.ts
ui/vite.config.ts → dev proxy /api → 8787; build → ../src/api/static/
src/api/static/  → production assets served by beak-flow (gitignored except .gitkeep)
```

Build commands:

| From | Command |
|------|---------|
| Repo root | `beak-flow build-ui` |
| `ui/` | `npm run build` (same output path) |

## Troubleshooting

| Issue | Check |
|-------|--------|
| UI cannot load tasks | Is `beak-flow` running on 8787? |
| AI Organise fails | `t ai doctor`, API keys, `ai.enabled` in config |
| Empty calendar | Tasks need `due_date` set; inbox items have no date |
| CORS errors | Use Vite dev server (proxy) or built UI via `beak-flow` |
| Blank page at `/` | Run `beak-flow build-ui` |
| UI missing after pip install | Build UI once, or use a wheel that includes `src/api/static/` |

## Related docs

- [api.md](api.md) — REST endpoints  
- [commands.md](commands.md) — CLI and config  
- [architecture.md](architecture.md) — codebase structure  
