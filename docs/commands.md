# Felicity Todos — Command Reference

Quick index: [docs/README.md](README.md) · Beak Flow UI: [beak-flow.md](beak-flow.md) · REST API: [api.md](api.md)

## Data locations

All paths use `Path.home() / ".todos"` (Linux, macOS, Windows).

| File | Purpose |
|------|---------|
| `todos.db` | SQLite database |
| `config.toml` | AI provider and model settings |

```bash
t init          # creates DB + default config
t config path   # print config file path
```

## Core CLI commands

| Command | Description | Example |
|---------|-------------|---------|
| `t init` | Initialize database and config | `t init` |
| `t a -m <msg>` | Add todo | `t a -m "Buy groceries"` |
| `t a -p <0-3>` | Priority | `t a -m "Fix bug" -p 3` |
| `t a -c <name>` | Category | `t a -c "Work"` |
| `t a -d <date>` | Due date | `t a -d "2026-06-15"` |
| `t l` | List todos | `t l` |
| `t l -t` | Table view | `t l -t` |
| `t l --overdue` | Overdue only | `t l --overdue` |
| `t e <id>` | Edit todo | `t e 5 -m "New title" -p 2` |
| `t done <id>` | Mark complete | `t done 5` |
| `t undo <id>` | Mark incomplete | `t undo 5` |
| `t rm <id>` | Delete todo | `t rm 3` |
| `t search <kw>` | Keyword search | `t search "proposal"` |
| `t stats` | Statistics | `t stats` |
| `t export <file>` | CSV export | `t export ~/todos.csv` |
| `t import <file>` | CSV import | `t import ~/todos.csv` |

### Categories

| Command | Description |
|---------|-------------|
| `t ac <name>` | Add category |
| `t ec <id> <name>` | Rename category |
| `t lc` | List categories |
| `t rmc <id>` | Remove category (todos → General) |

### Notes

| Command | Description |
|---------|-------------|
| `t n <id> <text>` | Add note |
| `t ln <id>` | List notes |

## Config commands (`t config`)

| Command | Description |
|---------|-------------|
| `t config show` | Effective config (JSON) |
| `t config path` | Path to `config.toml` |
| `t config get <key>` | e.g. `ai.provider` |
| `t config set <key> <val>` | e.g. `ai.provider openai` |
| `t config edit` | Open in `$EDITOR` |

Example `~/.todos/config.toml`:

```toml
[ai]
enabled = true
provider = "auto"
model = "gpt-4o-mini"
temperature = 0.2
show_provider_on_use = true

[harness]
codex_bin = "codex"
claude_bin = "claude"
timeout_seconds = 120
```

## AI commands (`t ai`)

Setup:

```bash
t ai setup
t ai doctor
```

| Command | Description |
|---------|-------------|
| `t ai add "<text>"` | Natural language → create todo |
| `t ai add "<text>" --dry-run` | Preview only |
| `t ai add --provider openai "<text>"` | Override provider |
| `t ai plan [today\|tomorrow\|week]` | Suggested plan |
| `t ai summary` | Workload narrative |
| `t ai risks` | Risk bullets |
| `t ai search "<query>"` | Smart search |
| `t ai breakdown "<task>"` | Flat subtasks |
| `t ai chat` | Read-only REPL (`exit` to quit) |

### Provider subcommands

| Command | Description |
|---------|-------------|
| `t ai provider list` | Allowed providers + auto resolution |
| `t ai provider set <name>` | `auto`, `openai`, `anthropic`, `gemini`, `ollama`, `litellm`, `codex`, `claude`, `none` |

### Environment variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI via LiteLLM |
| `ANTHROPIC_API_KEY` | Anthropic via LiteLLM |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini via LiteLLM |
| `OLLAMA_API_BASE` | Local models |

### Provider resolution (`provider = auto`)

1. CLI `--provider` override  
2. Fixed value in config (not `auto`)  
3. `OPENAI_API_KEY`  
4. `ANTHROPIC_API_KEY`  
5. `GOOGLE_API_KEY` / `GEMINI_API_KEY`  
6. `OLLAMA_API_BASE`  
7. Harness **only** if config explicitly `codex` or `claude`  

Harness is **never** auto-selected when API keys exist.

## Beak Flow (web UI)

| Command | Description |
|---------|-------------|
| `beak-flow` | Run server in foreground (default) |
| `beak-flow run` | Same as above |
| `beak-flow run --host HOST --port PORT` | Bind address (also env `BEAK_FLOW_HOST` / `BEAK_FLOW_PORT`) |
| `beak-flow build-ui` | Build Vue UI into `src/api/static/` |
| `beak-flow install-service` | Install OS background service |
| `beak-flow uninstall-service` | Remove OS service |
| `beak-flow service-status` | Show service + config summary |

Config file: `~/.todos/beak-flow.toml` (written on `install-service`).

UI hot reload (development):

```bash
cd ui && npm install && npm run dev
```

See [beak-flow.md](beak-flow.md).

## Integrations (GitHub)

| Command | Description |
|---------|-------------|
| `t integrations github setup` | Create `~/.todos/integrations/github.toml` |
| `t integrations github doctor` | Verify token and repos |
| `t integrations github sync` | Sync issues/PRs (bidirectional state) |
| `t integrations github repos list` | List configured repos |
| `t integrations github repos add org/repo` | Add a repository |
| `t integrations github link ID URL` | Link todo to issue/PR |
| `t integrations github unlink ID` | Remove GitHub link |

See [integrations/github.md](integrations/github.md).

## Tags

| Command | Description |
|---------|-------------|
| `t tag list` | List all tags |
| `t tag add ID name [names...]` | Add tags to a todo |

## Priority levels

| Value | Label | Color |
|-------|-------|-------|
| 0 | Low | Blue |
| 1 | Medium | Yellow |
| 2 | High | Orange |
| 3 | Critical | Red |

## Architecture notes

- Service layer: `src/services/`  
- AI providers: `src/ai/` (LiteLLM + optional harness)  
- CLI must not duplicate SQL — use services  

Details: [architecture.md](architecture.md).
