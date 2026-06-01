# Beak Flow UI

Vue 3 + TypeScript + Vite frontend for the Beak Flow planning gateway. It talks to the FastAPI backend via relative `/api` URLs (same origin in production).

## Prerequisites

- Node.js 18+
- Python package installed (`pip install -e .` from repo root)
- API running for dev: `beak-flow` on port **8787**

## Scripts

| Command | Purpose |
|---------|-------------|
| `npm run dev` | Vite dev server at http://localhost:5173 (proxies `/api` → 8787) |
| `npm run build` | Production build (also run via `beak-flow build-ui` from repo root) |
| `npm run preview` | Preview production build locally (optional) |

## Build output

Production builds are written to **`../src/api/static/`** (not `ui/dist`). FastAPI serves that directory when you run `beak-flow`.

From the repo root (recommended):

```bash
beak-flow build-ui
beak-flow
```

Open http://127.0.0.1:8787/

From this directory:

```bash
npm install
npm run build
cd .. && beak-flow
```

## Development workflow

Two terminals:

```bash
# Terminal 1 — repo root
beak-flow

# Terminal 2 — this directory
npm install
npm run dev
```

Edit Vue files with hot reload at http://localhost:5173. API calls go through the Vite proxy in [`vite.config.ts`](vite.config.ts).

## Project layout

```text
ui/
├── src/
│   ├── App.vue              # Shell + mobile tabs
│   ├── main.ts
│   ├── styles.css
│   ├── api/client.ts        # fetch /api/* (relative URLs)
│   ├── stores/
│   │   ├── planner.ts
│   │   └── reports.ts       # weekly report draft state
│   └── components/
│       ├── BrainDumpPanel.vue
│       ├── CalendarStrip.vue
│       ├── DayView.vue
│       ├── SourceFilterPanel.vue  # GitHub org/repo + tags
│       ├── TaskCard.vue           # shows display_source + tags
│       ├── TaskDetailModal.vue
│       ├── ReportsPanel.vue     # weekly report draft + send
│       └── AiDrawer.vue
├── vite.config.ts           # outDir → ../src/api/static
└── package.json
```

## Configuration

| Variable | Effect |
|----------|--------|
| `BEAK_FLOW_REPO_ROOT` | Repo root if `ui/` is not at default path (used by `beak-flow build-ui`) |
| `BEAK_FLOW_STATIC_DIR` | Override static directory served by FastAPI |

Server host/port/log: `~/.todos/beak-flow.toml` (see [../docs/beak-flow.md](../docs/beak-flow.md)).

## GitHub filters in the UI

The **Sources** panel (top of the left column) loads:

- `/api/integrations/github/sources` — org → repo tree
- `/api/tags` — tag list with counts

Use **Sync GitHub** to run `POST /api/integrations/github/sync`. Task cards show lines like:

`[GitHub] [beak-insights/beak-lims] #1025`

## Weekly reports

Use the **Reports** tab: generate a draft from todos/GitHub data, preview, then send via Resend. Configure `[email]` in `~/.todos/config.toml` and set `RESEND_API_KEY`.

## Related documentation

- [../docs/beak-flow.md](../docs/beak-flow.md) — UI workflows, service install, troubleshooting
- [../docs/integrations/email.md](../docs/integrations/email.md) — Resend setup and draft-first send
- [../docs/integrations/github.md](../docs/integrations/github.md) — GitHub sync setup
- [../docs/api.md](../docs/api.md) — REST endpoints
- [../docs/architecture.md](../docs/architecture.md) — Backend + data flow
