# Felicity Todos — Command Reference

## Core commands

See [README](../README.md) for task management, categories, notes, export/import, and stats.

The database and config live under `~/.todos/` (OS-agnostic):

| File | Purpose |
|------|---------|
| `todos.db` | SQLite database |
| `config.toml` | AI and app settings |

`t init` creates both the database and default config.

## Config commands

| Command | Description |
|---------|-------------|
| `t config show` | Print effective configuration (JSON) |
| `t config path` | Print path to `config.toml` |
| `t config get <key>` | Get value, e.g. `ai.provider` |
| `t config set <key> <value>` | Set value, e.g. `ai.provider openai` |
| `t config edit` | Open config in `$EDITOR` |

## AI commands

| Command | Description |
|---------|-------------|
| `t ai setup` | Create `~/.todos/` and default `config.toml` |
| `t ai doctor` | Show API keys, harness CLIs, resolved provider |
| `t ai add "<text>"` | Parse natural language → create todo |
| `t ai add "<text>" --dry-run` | Preview parsed fields only |
| `t ai add --provider openai "<text>"` | Override provider for one command |
| `t ai plan [today\|tomorrow\|week]` | Suggested focus plan from open tasks |
| `t ai summary` | Narrative workload summary |
| `t ai risks` | Deadline and workload risk bullets |
| `t ai search "<query>"` | LLM keyword rewrite + SQL search |
| `t ai breakdown "<task>"` | Create flat subtasks as separate todos |
| `t ai chat` | Read-only REPL (type `exit` to quit) |

### Provider subcommands

| Command | Description |
|---------|-------------|
| `t ai provider list` | Allowed providers and auto resolution |
| `t ai provider set <name>` | `auto`, `openai`, `anthropic`, `gemini`, `ollama`, `litellm`, `codex`, `claude`, `none` |

## Environment variables

| Variable | Used for |
|----------|----------|
| `OPENAI_API_KEY` | OpenAI via LiteLLM |
| `ANTHROPIC_API_KEY` | Anthropic via LiteLLM |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini via LiteLLM |
| `OLLAMA_API_BASE` | Local OpenAI-compatible server |

## Architecture

- **Direct mode:** `LiteLLMProvider` — default for structured JSON (`ParsedTask`, `PlanResponse`, etc.)
- **Harness mode:** subprocess to `codex` or `claude` — only when explicitly configured
- **Resolver:** `src/ai/resolver.py` — env + config + `--provider` override

Todo commands never call LiteLLM directly; they use `complete_json()` on the resolved `AIProvider`.
