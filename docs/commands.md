

## Implementation Details

A comprehensive todo CLI application with the following key implementation details:

### Core Features
- **Database Structure**: SQLite database stored at `~/.todos/todos.db` with tables for todos, categories, and notes
- **Priority System**: Color-coded priority levels (0=Low/Blue, 1=Medium/Yellow, 2=High/Orange, 3=Critical/Red)
- **Category Management**: Add, edit, delete categories and assign tasks to them
- **Command Structure**: All commands accessible via the `t` command with appropriate subcommands

### Additional Features
1. **Due Dates**: Set and filter tasks by due dates, with overdue tasks highlighted in red
2. **Completion Status**: Mark tasks as complete/incomplete and filter by status
3. **Notes System**: Add and view notes associated with tasks
4. **Search**: Search for tasks by keyword
5. **Export/Import**: Export tasks to CSV files and import them back
6. **Statistics**: View statistics about your tasks (counts by priority, category, etc.)

### Usage Guide & Cheat Sheet

## Installation

```bash
pip install felicity-todos
```

After installation, the `t` command will be available in your terminal.

## First-time Setup

Initialize the database before first use:

```bash
t init
```

This creates the necessary database file at `~/.todos/todos.db`.

## Commands Cheat Sheet

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `t init` | Initialize database | `t init` |
| `t a -m <message>` | Add a todo | `t a -m "Buy groceries"` |
| `t a -m <message> -p <priority>` | Add with priority (0-3) | `t a -m "Fix bug" -p 3` |
| `t a -m <message> -c <category>` | Add with category | `t a -m "Call John" -c "Personal"` |
| `t a -m <message> -d <date>` | Add with due date | `t a -m "Report" -d "2025-04-25"` |
| `t l` | List all todos | `t l` |
| `t e <id> <message>` | Edit todo message | `t e 5 "Updated task"` |
| `t rm <id>` | Remove a todo | `t rm 3` |

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

## Priority Levels

- **0**: Low (Blue)
- **1**: Medium (Yellow) 
- **2**: High (Orange)
- **3**: Critical (Red)

## Tips

1. Always run `t init` after installation to set up the database.
2. Use categories to organize related tasks.
3. Set priorities for better task management.
4. Use due dates for time-sensitive tasks.
5. Add notes to tasks for additional details.
6. Use `t stats` to get an overview of your tasks.

## Examples

Add a critical task due tomorrow:
```bash
t a -m "Complete project proposal" -p 3 -d "tomorrow"
```

List all high-priority work tasks:
```bash
t l -p 2 -c "Work"
```

Add a note to task #5:
```bash
t n 5 "Don't forget to include the appendix"
```
