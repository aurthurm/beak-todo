# REST API Reference

Base URL: `http://127.0.0.1:8787` (default host/port; see `~/.todos/beak-flow.toml`)

Interactive docs: `http://127.0.0.1:8787/docs` (OpenAPI / Swagger)

All JSON endpoints are under `/api`.

| Mode | How the UI reaches the API |
|------|----------------------------|
| **Production** | `beak-flow build-ui && beak-flow` — UI and API on the same origin; browser calls `/api/*` |
| **Development** | Vite on :5173 proxies `/api` → 8787 while `beak-flow` runs in another terminal |

See [beak-flow.md](beak-flow.md) and [../ui/README.md](../ui/README.md).

## Health

### `GET /api/health`

```json
{
  "status": "ok",
  "ai_enabled": true,
  "config_path": "/home/user/.todos/config.toml"
}
```

## Todos

### `GET /api/todos`

Query parameters (combine as needed):

| Param | Type | Description |
|-------|------|-------------|
| `inbox` | bool | `due_date` null, incomplete |
| `due_date` | string | Exact date `YYYY-MM-DD` |
| `due_from` | string | Range start (inclusive) |
| `due_to` | string | Range end (inclusive) |
| `completed` | bool | Filter by completion |
| `category` | string | Category name |
| `search` | string | `LIKE` on message and category |
| `overdue` | bool | Past due, incomplete |
| `source` | string | `local` or `github` |
| `organisation` | string | GitHub org (with `source=github`) |
| `repository` | string | GitHub repo name |
| `item_type` | string | `issue` or `pr` |
| `external_state` | string | e.g. `open`, `closed`, `merged` |
| `tag` | string | Repeat for AND filter on tags |

**Example:** calendar week

```http
GET /api/todos?due_from=2026-06-01&due_to=2026-06-14&completed=false
```

**Response:** array of `TodoOut`

```json
{
  "id": 1,
  "message": "Finish proposal",
  "priority": 3,
  "priority_label": "Critical",
  "priority_color": "red",
  "category": "Work",
  "completed": false,
  "due_date": "2026-06-05",
  "sort_order": 0,
  "source_type": "github",
  "external": {
    "provider": "github",
    "organisation": "beak-insights",
    "repository": "beak-lims",
    "item_type": "issue",
    "item_number": 1025,
    "state": "open",
    "url": "https://github.com/beak-insights/beak-lims/issues/1025"
  },
  "tags": ["lims", "bug"],
  "display_source": "[GitHub] [beak-insights/beak-lims] #1025"
}
```

### `GET /api/todos/{id}`

Single todo.

### `POST /api/todos`

```json
{
  "message": "New task",
  "priority": 2,
  "category": "Work",
  "due_date": "2026-06-10"
}
```

### `PATCH /api/todos/{id}`

Partial update. All fields optional.

```json
{
  "message": "Updated title",
  "priority": 1,
  "category": "Personal",
  "due_date": "2026-06-12",
  "clear_due": false,
  "completed": false,
  "sort_order": 2
}
```

Set `clear_due: true` to move task to **inbox** (removes due date).

### `DELETE /api/todos/{id}`

Deletes todo and its notes. Returns `204`.

### `POST /api/todos/reorder`

Batch update `sort_order` for day-view ordering.

```json
{
  "items": [
    { "id": 1, "sort_order": 0 },
    { "id": 2, "sort_order": 1 }
  ]
}
```

### Notes

| Method | Path | Body |
|--------|------|------|
| `GET` | `/api/todos/{id}/notes` | — |
| `POST` | `/api/todos/{id}/notes` | `{ "content": "..." }` |

## Categories

### `GET /api/categories`

```json
[
  { "id": 1, "name": "General", "todo_count": 5 }
]
```

## AI

Requires AI enabled in config and a configured provider (see [commands.md](commands.md)).

Errors return `503` with message when AI is unavailable.

### `POST /api/ai/brain-dump`

Parse messy text into structured tasks (preview only).

```json
{ "text": "finish proposal by Friday\ncall client tomorrow", "provider": null }
```

**Response:**

```json
{
  "tasks": [
    {
      "message": "Finish proposal",
      "priority": 3,
      "category": "Work",
      "due_date": "2026-06-05"
    }
  ]
}
```

### `POST /api/ai/brain-dump/apply`

Create todos from accepted suggestions.

```json
{
  "tasks": [ { "message": "...", "priority": 2, "category": "Work", "due_date": null } ]
}
```

**Response:** `{ "ids": [12, 13] }`

### `POST /api/ai/plan`

```json
{ "horizon": "today", "provider": null }
```

Horizon: `today`, `tomorrow`, or `week`.

**Response:** `PlanResponse` with `items[]` and `summary`.

### `POST /api/ai/summary`

Workload narrative. Optional query `provider`.

### `POST /api/ai/risks`

Risk bullets from stats heuristics + LLM.

### `POST /api/ai/chat`

Single-turn assistant (read-only context).

```json
{ "message": "What should I focus on today?", "provider": null }
```

**Response:** `{ "answer": "..." }`

### `POST /api/ai/actions/preview`

Propose task patches (reschedule, etc.). UI shows preview before apply.

```json
{ "request": "Move low-priority tasks to next week", "provider": null }
```

**Response:**

```json
{
  "description": "Move 3 tasks to next week",
  "patches": [
    { "todo_id": 5, "due_date": "2026-06-10", "clear_due": false }
  ]
}
```

### `POST /api/ai/actions/apply`

```json
{
  "patches": [
    { "todo_id": 5, "due_date": "2026-06-10" }
  ]
}
```

**Response:** `{ "applied": 1 }`

## Drag-and-drop mapping (UI)

| User action | API call |
|-------------|----------|
| Drop on day column | `PATCH` with `due_date` |
| Drop on inbox | `PATCH` with `clear_due: true` |
| Drop on done | `PATCH` with `completed: true` |
| Reorder in day view | `POST /api/todos/reorder` |

## Tags

### `GET /api/tags`

List tags with todo counts.

### `PUT /api/todos/{id}/tags`

```json
{ "tags": ["bug", "urgent", "lims"] }
```

## GitHub integration

### `GET /api/integrations/github/sources`

Org → repos tree from database.

### `GET /api/integrations/github/status`

Configured repo count and doctor messages.

### `POST /api/integrations/github/sync`

Runs bidirectional sync. Response: `{ "created", "updated", "pushed", "errors" }`.

### `POST /api/todos/{id}/external-link`

```json
{ "url": "https://github.com/org/repo/issues/42" }
```

### `DELETE /api/todos/{id}/external-link`

Removes link; local todo remains.

See [integrations/github.md](integrations/github.md).
