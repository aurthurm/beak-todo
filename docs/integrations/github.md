# GitHub integration

Sync GitHub **issues** and **pull requests** into local todos with structured org/repo identity and optional **tags** from GitHub labels.

## Setup

```bash
export GITHUB_TOKEN="ghp_..."
t integrations github setup
# Edit ~/.todos/integrations/github.toml — replace your-org/your-repo
t integrations github repos add beak-insights/beak-lims
t integrations github doctor
t integrations github sync
```

Token needs `repo` scope (private repos) or `public_repo` for public repositories.

## Config file

`~/.todos/integrations/github.toml`:

```toml
token_env = "GITHUB_TOKEN"
sync_title_to_github = false

[[repos]]
organisation = "beak-insights"
repository = "beak-lims"
enabled = true
sync_issues = true
sync_prs = true
```

## Sync behaviour

| Field | GitHub → local | Local → GitHub |
|-------|----------------|----------------|
| Title | Updated on sync | Only if `sync_title_to_github = true` |
| Open/closed | Sets `completed` on todo | Completing todo closes/reopens issue |
| Due date, priority, sort | Never from GitHub | Never pushed |
| Labels | Imported as **tags** | Not pushed in v1 |

**Auto-create:** each issue/PR without a link gets a new local todo.

**Manual link:** `t integrations github link <todo_id> <url>` or `POST /api/todos/{id}/external-link`.

**Unlink:** keeps the local todo; removes GitHub association only.

## Filtering

```bash
t l  # use API/Beak Flow filters:
# source=github&organisation=beak-insights&repository=beak-lims
# tag=bug&tag=urgent  (AND)
```

## Beak Flow UI

- **Sources** panel: Local / GitHub / per-repo filters
- **Sync GitHub** button
- Task cards show `display_source` line

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `doctor` fails token | Set `GITHUB_TOKEN`, check scopes |
| Sync errors for one repo | Verify access to org/repo |
| Duplicate todos | One external item links to one todo; unlink duplicates manually |
