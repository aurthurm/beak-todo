# Felicity Todos

A powerful, feature-rich command-line todo application with a beautiful interface and comprehensive task management capabilities.

![Demo](demo.gif)

## Features

- 🎨 **Color-coded Priority System**
  - Low (Blue)
  - Medium (Yellow)
  - High (Orange)
  - Critical (Red)

- 📝 **Task Management**
  - Add, edit, and remove tasks
  - Set priorities and due dates
  - Mark tasks as complete/incomplete
  - Add notes to tasks
  - Search functionality

- 📂 **Category System**
  - Create and manage categories
  - Assign tasks to categories
  - Filter by category

- 📊 **Multiple View Options**
  - Default colored line view
  - Detailed table view
  - Statistics and overview

- 🔄 **Data Management**
  - Export/Import to CSV
  - SQLite database backend
  - Automatic backup support

- 🤖 **AI Features** (optional)
  - Natural language task creation (`t ai add`)
  - Daily planning assistant (`t ai plan`)
  - Summaries, risk detection, smart search
  - Task breakdown and read-only chat
  - Dual-mode providers: direct API (LiteLLM) or harness CLI (Codex/Claude, opt-in)

## Installation

```bash
pip install felicity-todos
```

## Quick Start

1. Initialize the database (creates `~/.todos/` and default config):
```bash
t init
```

2. Add your first task:
```bash
t a -m "Complete project proposal" -p 3 -d "2024-03-20"
```

3. View your tasks:
```bash
t l
```

## Usage

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `t init` | Initialize database | `t init` |
| `t a -m <message>` | Add a todo | `t a -m "Buy groceries"` |
| `t a -m <message> -p <priority>` | Add with priority (0-3) | `t a -m "Fix bug" -p 3` |
| `t a -m <message> -c <category>` | Add with category | `t a -m "Call John" -c "Personal"` |
| `t a -m <message> -d <date>` | Add with due date | `t a -m "Report" -d "2024-03-25"` |
| `t l` | List all todos | `t l` |
| `t e <id> <message>` | Edit todo message | `t e 5 "Updated task"` |
| `t rm <id>` | Remove a todo | `t rm 3` |

### View Options

#### Default View
The default view displays tasks in a colored line format, where the entire line is colored according to the task's priority:

```bash
t l
```

Output example:
```
#1 Work Complete project proposal 2024-03-20 ✓
#2 Personal Buy groceries
#3 Work Fix critical bug 2024-03-18
```

#### Table View
For a more detailed view, use the table format:

```bash
t l -t
```

This displays tasks in a table with columns for ID, Message, Priority, Category, Due Date, and Status.

### Category Management

| Command | Description | Example |
|---------|-------------|---------|
| `t ac <name>` | Add a category | `t ac "Work"` |
| `t ec <id> <name>` | Edit category name | `t ec 2 "Personal"` |
| `t lc` | List all categories | `t lc` |
| `t rmc <id>` | Remove a category | `t rmc 3` |

### Filtering & Searching

| Command | Description | Example |
|---------|-------------|---------|
| `t l -p <priority>` | List by priority | `t l -p 2` |
| `t l -c <category>` | List by category | `t l -c "Work"` |
| `t l -p <priority> -c <category>` | Filter by both | `t l -p 3 -c "Work"` |
| `t l --done` | Show completed | `t l --done` |
| `t l --undone` | Show incomplete | `t l --undone` |
| `t l -d` | Sort by due date | `t l -d` |
| `t l --overdue` | Show overdue | `t l --overdue` |
| `t l -t` | Display in table format | `t l -t` |
| `t search <keyword>` | Search todos | `t search "meeting"` |

### Task Status

| Command | Description | Example |
|---------|-------------|---------|
| `t done <id>` | Mark as completed | `t done 5` |
| `t undo <id>` | Mark as not completed | `t undo 5` |

### Notes

| Command | Description | Example |
|---------|-------------|---------|
| `t n <id> <content>` | Add note to todo | `t n 4 "Remember to add examples"` |
| `t ln <id>` | List notes for todo | `t ln 4` |

### Utilities

| Command | Description | Example |
|---------|-------------|---------|
| `t stats` | Show statistics | `t stats` |
| `t export <filename>` | Export todos to CSV | `t export ~/todos.csv` |
| `t import <filename>` | Import todos from CSV | `t import ~/todos.csv` |

### AI Commands

Requires an API key (recommended) or explicit harness configuration.

```bash
# Setup and diagnostics
t ai setup
t ai doctor

# Natural language add
t ai add "Submit MoHCC proposal by Friday urgent"

# Planning and insights
t ai plan today
t ai summary
t ai risks
t ai search "proposals due soon"
t ai breakdown "Prepare Facility Registry proposal"
t ai chat

# Provider management
t ai provider list
t ai provider set openai   # or anthropic, auto, codex, claude, none
```

Use `--dry-run` on `t ai add` and `t ai breakdown` to preview without saving.

### Configuration (`~/.todos/config.toml`)

OS-agnostic paths via `Path.home() / ".todos"`.

```bash
t config show
t config path
t config get ai.provider
t config set ai.provider anthropic
t config set ai.model "anthropic/claude-3-5-haiku-latest"
t config edit
```

**Direct API mode (default):** set one of:

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export GOOGLE_API_KEY="..."
export OLLAMA_API_BASE="http://localhost:11434"   # local models
```

Provider resolution order when `ai.provider = auto`:

1. Configured provider (if not `auto`)
2. `OPENAI_API_KEY` → LiteLLM
3. `ANTHROPIC_API_KEY` → LiteLLM
4. `GOOGLE_API_KEY` / `GEMINI_API_KEY` → LiteLLM
5. `OLLAMA_API_BASE` → LiteLLM
6. Harness only if explicitly set (`t ai provider set codex`)

**Harness mode (opt-in):** Codex or Claude CLI. Never auto-selected when API keys exist (avoids unexpected billing). Set explicitly:

```bash
t ai provider set codex
t ai add --provider claude "Review LIMS tasks tomorrow"
```

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

## Priority Levels

- **0**: Low (Blue)
- **1**: Medium (Yellow)
- **2**: High (Orange)
- **3**: Critical (Red)

## Examples

### Adding a Task with All Options
```bash
t a -m "Complete project proposal" -p 3 -c "Work" -d "2024-03-20"
```

### Filtering Tasks
```bash
# Show all high-priority work tasks
t l -p 2 -c "Work"

# Show overdue tasks in table format
t l --overdue -t

# Show completed personal tasks
t l -c "Personal" --done
```

### Managing Categories
```bash
# Create a new category
t ac "Projects"

# List tasks in a specific category
t l -c "Projects"

# Edit category name
t ec 1 "Active Projects"
```

### Adding Notes
```bash
# Add a note to task #5
t n 5 "Don't forget to include the appendix"

# View notes for task #5
t ln 5
```

## Tips

1. **Organization**: Use categories to group related tasks
2. **Priorities**: Set appropriate priorities to manage task importance
3. **Due Dates**: Always set due dates for time-sensitive tasks
4. **Notes**: Use notes for additional details and context
5. **Regular Updates**: Use `t stats` to get an overview of your tasks
6. **Backup**: Regularly export your tasks using `t export`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 