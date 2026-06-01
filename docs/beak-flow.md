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
- Node.js 18+ (for UI development/build only)

### Development (two terminals)

```bash
# From repo root
pip install -e .

# Terminal 1 — API
beak-flow
# equivalent: uvicorn src.api.app:app --reload --port 8787

# Terminal 2 — UI with hot reload
cd ui && npm install && npm run dev
```

- UI: http://localhost:5173  
- API: http://127.0.0.1:8787  
- OpenAPI: http://127.0.0.1:8787/docs  

Vite proxies `/api` → `8787`.

### Production-style (single port)

```bash
cd ui && npm run build
beak-flow
```

When `ui/dist` exists, FastAPI serves the built UI from the same port as the API.

### AI setup

Brain dump and the AI drawer need a provider:

```bash
export OPENAI_API_KEY="..."
t ai doctor          # verify resolution
```

Or configure in `~/.todos/config.toml` (see [commands.md](commands.md)).

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

```text
ui/
├── src/
│   ├── App.vue
│   ├── api/client.ts
│   ├── stores/planner.ts
│   └── components/
│       ├── BrainDumpPanel.vue
│       ├── CalendarStrip.vue
│       ├── DayView.vue
│       ├── TaskCard.vue
│       ├── TaskDetailModal.vue
│       └── AiDrawer.vue
├── vite.config.ts
└── package.json
```

## Troubleshooting

| Issue | Check |
|-------|--------|
| UI cannot load tasks | Is `beak-flow` running on 8787? |
| AI Organise fails | `t ai doctor`, API keys, `ai.enabled` in config |
| Empty calendar | Tasks need `due_date` set; inbox items have no date |
| CORS errors | Use Vite dev server (proxy) or built UI via `beak-flow` |

## Related docs

- [api.md](api.md) — REST endpoints  
- [commands.md](commands.md) — CLI and config  
- [architecture.md](architecture.md) — codebase structure  
