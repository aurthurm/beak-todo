# Architecture

Felicity Todos is a **terminal-first todo engine** with an optional **Beak Flow** planning gateway (Vue + FastAPI). Both layers share one SQLite database.

## Data flow

```text
                    ~/.todos/
                    ├── todos.db      (SQLite)
                    └── config.toml   (AI settings)

                           │
                           ▼
              ┌────────────────────────┐
              │   src/services/        │
              │   todos, notes,        │
              │   categories,          │
              │   ai_service           │
              └───────────┬────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   src/main.py      src/api/app.py    (tests)
   Typer CLI        FastAPI REST
   command `t`      command `beak-flow`
                          │
                          ▼
                     ui/ (Vue 3)
                     Beak Flow UI
```

## Directory layout

```text
beak-todo/
├── src/
│   ├── main.py              # Typer CLI entry (`t`)
│   ├── config.py            # ~/.todos/config.toml
│   ├── config_cli.py        # `t config` commands
│   ├── todos.py             # Re-exports (CLI backward compat)
│   ├── db/
│   │   └── connection.py    # init, migrate, connections
│   ├── services/
│   │   ├── todos.py         # CRUD, inbox, date range, sort_order
│   │   ├── notes.py
│   │   ├── categories.py
│   │   ├── external.py
│   │   ├── tags.py
│   │   └── ai_service.py    # Brain dump, plan, actions preview
│   ├── integrations/          # github/ (+ future providers)
│   ├── api/
│   │   ├── app.py           # FastAPI app + static UI mount
│   │   ├── static/          # Built UI (beak-flow build-ui)
│   │   ├── static_paths.py  # resolve_static_dir()
│   │   ├── server.py        # beak-flow CLI (run, build-ui, service)
│   │   ├── server_config.py # ~/.todos/beak-flow.toml
│   │   ├── service_install.py
│   │   ├── schemas.py       # API DTOs
│   │   └── routes/          # todos, categories, ai
│   └── ai/                  # LiteLLM + harness providers
├── ui/                      # Vue 3 + Vite frontend
├── tests/
└── docs/
```

## Database schema

### Integrations (Option B)

```text
external_sources     provider + organisation + repository
external_items       issue/pr per source (title, state, url)
todo_external_links  todo_id → external_item_id (0..1 per todo)
tags / todo_tags     many-to-many context labels
```

Planning stays on `todos` (due_date, priority, sort_order, completed). Org/repo are **not** tags.

### `categories`

| Column | Type |
|--------|------|
| id | INTEGER PK |
| name | TEXT UNIQUE |

Default category: `General` (id = 1).

### `todos`

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| message | TEXT | Task title |
| priority | INTEGER | 0–3 |
| category_id | INTEGER FK | |
| completed | BOOLEAN | |
| created_at | TIMESTAMP | |
| due_date | TEXT | ISO `YYYY-MM-DD` or NULL (inbox) |
| sort_order | INTEGER | Within-day ordering in UI |

**Inbox** (UI/API): `due_date IS NULL AND completed = 0`.

### `notes`

| Column | Type |
|--------|------|
| id | INTEGER PK |
| todo_id | INTEGER FK |
| content | TEXT |
| created_at | TIMESTAMP |

Migrations run idempotently in `migrate_db()` when `sort_order` is missing.

## AI layer

| Mode | When | Implementation |
|------|------|----------------|
| Direct (default) | API keys in env | `LiteLLMProvider` |
| Harness (opt-in) | `t ai provider set codex` | Subprocess to CLI |

Resolver: `src/ai/resolver.py`. All structured output uses Pydantic schemas in `src/ai/schemas.py`.

## Design rules

1. **Single service layer** — CLI and API call `src/services/*`, not raw SQL in routes.
2. **Same database** — CLI changes appear in UI immediately (and vice versa).
3. **Preview before mutate (UI)** — AI drawer uses `/api/ai/actions/preview` then apply.
4. **No auth in v1** — Local-only, single user.
