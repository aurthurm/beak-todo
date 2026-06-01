import csv
import sqlite3
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from src.ai import ai_app
from src.config_cli import config_app
from src.integrations_cli import integrations_app
from src.tag_cli import tag_app
from src.todos import (
    PRIORITIES,
    ListFilters,
    create_todo,
    ensure_db,
    fetch_todos,
    format_due_date,
    get_category_id,
    get_category_name,
    get_db_connection,
    get_todo_completed,
    init_db,
    search_todos_single,
    update_todo,
    validate_due_date,
)

app = typer.Typer()
app.add_typer(config_app, name="config")
app.add_typer(ai_app, name="ai")
app.add_typer(integrations_app, name="integrations")
app.add_typer(tag_app, name="tag")
console = Console()


@app.callback()
def _app_callback():
    """Felicity Todos CLI."""
    ensure_db()


@app.command("a")
def add(
    message: str = typer.Option(..., "-m", "--message", help="Todo message"),
    priority: int = typer.Option(0, "-p", "--priority", help="Priority (0-3)"),
    category: str = typer.Option("General", "-c", "--category", help="Category name"),
    due: Optional[str] = typer.Option(None, "-d", "--due", help="Due date (YYYY-MM-DD)"),
):
    """Add a new todo."""
    if priority < 0 or priority > 3:
        typer.echo("Priority must be between 0 and 3")
        raise typer.Exit(1)

    due_date = None
    if due:
        try:
            due_date = validate_due_date(due)
        except ValueError as e:
            typer.echo(str(e))
            raise typer.Exit(1)

    todo_id = create_todo(message, priority, category, due_date)
    typer.echo(f"Added todo #{todo_id}: {message}")


@app.command("ac")
def add_category(name: str):
    """Add a new category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        category_id = cursor.lastrowid
        conn.commit()
        typer.echo(f"Added category #{category_id}: {name}")
    except sqlite3.IntegrityError:
        typer.echo(f"Category '{name}' already exists")
    conn.close()


@app.command("e")
def edit(
    id: int,
    message: Optional[str] = typer.Option(None, "-m", "--message", help="Todo message"),
    priority: Optional[int] = typer.Option(None, "-p", "--priority", help="Priority (0-3)"),
    category: Optional[str] = typer.Option(None, "-c", "--category", help="Category name"),
    due: Optional[str] = typer.Option(None, "-d", "--due", help="Due date (YYYY-MM-DD)"),
):
    """Edit a todo."""
    if get_todo_completed(id) is None:
        typer.echo(f"Todo #{id} not found")
        raise typer.Exit(1)

    if priority is not None and (priority < 0 or priority > 3):
        typer.echo("Priority must be between 0 and 3")
        raise typer.Exit(1)

    clear_due = due is not None and due.lower() == "none"
    due_val = None if clear_due else due

    if message is None and priority is None and category is None and due is None:
        typer.echo("No changes specified")
        raise typer.Exit(1)

    try:
        ok = update_todo(
            id,
            message=message,
            priority=priority,
            category=category,
            due=due_val,
            clear_due=clear_due,
        )
    except ValueError as e:
        typer.echo(str(e))
        raise typer.Exit(1)

    if not ok:
        typer.echo(f"Todo #{id} not found")
        raise typer.Exit(1)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, message, priority, category_id, due_date FROM todos WHERE id = ?",
        (id,),
    )
    updated_todo = cursor.fetchone()
    conn.close()

    if updated_todo:
        category_name = get_category_name(updated_todo[3])
        due_date_str = format_due_date(updated_todo[4])
        priority_name = PRIORITIES[updated_todo[2]][0]
        typer.echo(f"Updated todo #{updated_todo[0]}: {updated_todo[1]}")
        typer.echo(f"  Priority: {priority_name}")
        typer.echo(f"  Category: {category_name}")
        if due_date_str:
            typer.echo(f"  Due: {due_date_str}")


@app.command("ec")
def edit_category(id: int, name: str):
    """Edit a category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (id,))
    category = cursor.fetchone()
    if not category:
        typer.echo(f"Category #{id} not found")
        conn.close()
        raise typer.Exit(1)
    try:
        cursor.execute("UPDATE categories SET name = ? WHERE id = ?", (name, id))
        conn.commit()
        typer.echo(f"Updated category #{id} to: {name}")
    except sqlite3.IntegrityError:
        typer.echo(f"Category '{name}' already exists")
    conn.close()


@app.command("l")
def list_todos(
    priority: Optional[int] = typer.Option(None, "-p", "--priority", help="Filter by priority"),
    category: Optional[str] = typer.Option(None, "-c", "--category", help="Filter by category"),
    done: bool = typer.Option(False, "--done", help="Show only completed todos"),
    undone: bool = typer.Option(False, "--undone", help="Show only incomplete todos"),
    due: bool = typer.Option(False, "-d", "--due", help="Sort by due date"),
    overdue: bool = typer.Option(False, "--overdue", help="Show only overdue todos"),
    table: bool = typer.Option(False, "-t", "--table", help="Display in table format"),
):
    """List todos with optional filtering."""
    filters = ListFilters(
        priority=priority,
        category=category,
        done=done,
        undone=undone,
        sort_by_due=due,
        overdue=overdue,
    )
    todos = fetch_todos(filters)

    if not todos:
        typer.echo("No todos found matching criteria")
        return

    if table:
        out_table = Table(show_header=True, header_style="bold")
        out_table.add_column("ID", style="bold")
        out_table.add_column("Message")
        out_table.add_column("Priority", style="bold")
        out_table.add_column("Category")
        out_table.add_column("Due Date")
        out_table.add_column("Status")

        for todo in todos:
            todo_id, message, prio, category_name, completed, due_date = todo
            category_name = category_name or "General"
            priority_name, priority_color = PRIORITIES[prio]
            priority_text = Text(priority_name, style=priority_color)
            id_text = Text(str(todo_id), style=priority_color)
            status = "✓" if completed else " "
            due_date_str = format_due_date(due_date)
            due_style = ""
            if due_date and not completed:
                try:
                    import datetime

                    due_date_obj = datetime.datetime.fromisoformat(due_date).date()
                    today = datetime.datetime.now().date()
                    if due_date_obj < today:
                        due_style = "red bold"
                except (ValueError, TypeError):
                    pass
            due_text = Text(due_date_str, style=due_style) if due_style else due_date_str
            out_table.add_row(id_text, message, priority_text, category_name, due_text, status)
        console.print(out_table)
    else:
        for todo in todos:
            todo_id, message, prio, category_name, completed, due_date = todo
            category_name = category_name or "General"
            _, priority_color = PRIORITIES[prio]
            status = "✓" if completed else " "
            due_date_str = format_due_date(due_date)
            line = f"#{todo_id} ({category_name}) {message}"
            if due_date_str:
                line += f" [{due_date_str}]"
            if status == "✓":
                line += " (✓)"
            console.print(Text(line, style=priority_color))


@app.command("lc")
def list_categories():
    """List all categories."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT c.id, c.name, COUNT(t.id) as todo_count
    FROM categories c
    LEFT JOIN todos t ON c.id = t.category_id
    GROUP BY c.id
    ORDER BY c.name
    """
    )
    categories = cursor.fetchall()
    conn.close()

    if not categories:
        typer.echo("No categories found")
        return

    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Name")
    table.add_column("Todo Count")
    for category in categories:
        table.add_row(str(category[0]), category[1], str(category[2]))
    console.print(table)


@app.command("done")
def mark_done(id: int):
    """Mark a todo as done."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET completed = 1 WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        typer.echo(f"Todo #{id} not found")
    else:
        typer.echo(f"Marked todo #{id} as done")
    conn.commit()
    conn.close()


@app.command("undo")
def mark_undone(id: int):
    """Mark a todo as not done."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET completed = 0 WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        typer.echo(f"Todo #{id} not found")
    else:
        typer.echo(f"Marked todo #{id} as not done")
    conn.commit()
    conn.close()


@app.command("rm")
def remove_todo(id: int):
    """Remove a todo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE todo_id = ?", (id,))
    cursor.execute("DELETE FROM todos WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        typer.echo(f"Todo #{id} not found")
    else:
        typer.echo(f"Removed todo #{id}")
    conn.commit()
    conn.close()


@app.command("rmc")
def remove_category(id: int):
    """Remove a category."""
    if id == 1:
        typer.echo("Cannot remove default 'General' category")
        raise typer.Exit(1)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET category_id = 1 WHERE category_id = ?", (id,))
    cursor.execute("DELETE FROM categories WHERE id = ?", (id,))
    if cursor.rowcount == 0:
        typer.echo(f"Category #{id} not found")
    else:
        typer.echo(f"Removed category #{id}")
    conn.commit()
    conn.close()


@app.command("n")
def add_note(id: int, content: str):
    """Add a note to a todo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM todos WHERE id = ?", (id,))
    todo = cursor.fetchone()
    if not todo:
        typer.echo(f"Todo #{id} not found")
        conn.close()
        raise typer.Exit(1)
    cursor.execute("INSERT INTO notes (todo_id, content) VALUES (?, ?)", (id, content))
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    typer.echo(f"Added note #{note_id} to todo #{id}")


@app.command("ln")
def list_notes(id: int):
    """List notes for a todo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message FROM todos WHERE id = ?", (id,))
    todo = cursor.fetchone()
    if not todo:
        typer.echo(f"Todo #{id} not found")
        conn.close()
        raise typer.Exit(1)
    cursor.execute(
        """
    SELECT id, content, created_at FROM notes WHERE todo_id = ? ORDER BY created_at
    """,
        (id,),
    )
    notes = cursor.fetchall()
    conn.close()
    if not notes:
        typer.echo(f"No notes found for todo #{id}: {todo[0]}")
        return
    typer.echo(f"Notes for todo #{id}: {todo[0]}")
    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Content")
    table.add_column("Created At")
    for note in notes:
        table.add_row(str(note[0]), note[1], note[2])
    console.print(table)


@app.command("search")
def search(keyword: str):
    """Search todos by keyword."""
    todos = search_todos_single(keyword)
    if not todos:
        typer.echo(f"No todos found matching '{keyword}'")
        return
    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Message")
    table.add_column("Priority")
    table.add_column("Category")
    table.add_column("Due Date")
    table.add_column("Status")
    for todo in todos:
        todo_id, message, prio, category_name, completed, due_date = todo
        category_name = category_name or "General"
        priority_name, priority_color = PRIORITIES[prio]
        priority_text = Text(priority_name, style=priority_color)
        status = "✓" if completed else " "
        due_date_str = format_due_date(due_date)
        table.add_row(
            Text(str(todo_id), style=priority_color),
            message,
            priority_text,
            Text(category_name, style=priority_color),
            Text(due_date_str, style=priority_color),
            Text(status, style=priority_color),
        )
    console.print(table)


@app.command("export")
def export_todos(filename: str):
    """Export todos to a CSV file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT t.id, t.message, t.priority, c.name, t.completed, t.due_date
    FROM todos t
    LEFT JOIN categories c ON t.category_id = c.id
    ORDER BY t.id
    """
    )
    todos = cursor.fetchall()
    conn.close()
    if not todos:
        typer.echo("No todos to export")
        return
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Message", "Priority", "Category", "Completed", "Due Date"])
        writer.writerows(todos)
    typer.echo(f"Exported {len(todos)} todos to {filename}")


@app.command("import")
def import_todos(filename: str):
    """Import todos from a CSV file."""
    try:
        with open(filename, "r", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            expected_header = ["ID", "Message", "Priority", "Category", "Completed", "Due Date"]
            if header != expected_header:
                typer.echo(f"Invalid CSV format. Expected header: {', '.join(expected_header)}")
                return
            imported = 0
            for row in reader:
                if len(row) != 6:
                    continue
                _, message, priority, category, completed, due_date = row
                try:
                    priority = int(priority)
                    if priority < 0 or priority > 3:
                        priority = 0
                except ValueError:
                    priority = 0
                completed = 1 if completed == "1" else 0
                if due_date in ("None", ""):
                    due_date = None
                create_todo(message, priority, category, due_date, completed=completed)
                imported += 1
            typer.echo(f"Imported {imported} todos")
    except FileNotFoundError:
        typer.echo(f"File {filename} not found")
    except Exception as e:
        typer.echo(f"Error importing todos: {e}")


@app.command("stats")
def show_stats():
    """Show statistics about todos."""
    from src.todos import fetch_stats_snapshot

    snap = fetch_stats_snapshot()
    typer.echo(f"Total todos: {snap['total']}")
    typer.echo(f"Completed: {snap['completed']}")
    typer.echo(f"Incomplete: {snap['incomplete']}")
    typer.echo(f"Overdue: {snap['overdue']}")
    typer.echo("\nTodos by priority:")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT priority, COUNT(*) FROM todos GROUP BY priority ORDER BY priority")
    for priority, count in cursor.fetchall():
        priority_name, priority_color = PRIORITIES[priority]
        console.print(Text(f"{priority_name}: {count}", style=priority_color))
    conn.close()
    typer.echo("\nTodos by category:")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
    SELECT c.name, COUNT(t.id)
    FROM categories c
    LEFT JOIN todos t ON c.id = t.category_id
    GROUP BY c.id
    ORDER BY COUNT(t.id) DESC
    """
    )
    for category, count in cursor.fetchall():
        typer.echo(f"{category}: {count}")
    conn.close()


@app.command("init")
def init():
    """Initialize the database and set up the application."""
    init_db()
    from src.config import ensure_default_config

    ensure_default_config()
    typer.echo("Database initialized successfully!")
    typer.echo("Application is ready to use!")


def main():
    app()


if __name__ == "__main__":
    main()
