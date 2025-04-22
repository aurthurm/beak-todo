import typer
import sqlite3
import datetime
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text
from dateutil.parser import parse as date_parse
from tabulate import tabulate

app = typer.Typer()
console = Console()

# Priority colors
PRIORITIES = {
    0: ("Low", "blue"),
    1: ("Medium", "yellow"),
    2: ("High", "orange"),
    3: ("Critical", "red"),
}

# Initialize database
def init_db():
    """Initialize the database if it doesn't exist."""
    # Create directory if it doesn't exist
    db_dir = Path.home() / ".todos"
    db_dir.mkdir(exist_ok=True)

    db_path = db_dir / "todos.db"
    
    # Connect to the database and create tables if they don't exist
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create categories table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
    ''')
    
    # Create todos table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS todos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        priority INTEGER DEFAULT 0,
        category_id INTEGER,
        completed BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        due_date TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    # Create notes table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        todo_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (todo_id) REFERENCES todos (id)
    )
    ''')
    
    # Ensure we have a default "General" category
    cursor.execute('INSERT OR IGNORE INTO categories (id, name) VALUES (1, "General")')
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Get a connection to the database."""
    db_path = Path.home() / ".todos" / "todos.db"
    return sqlite3.connect(str(db_path))

# Helper functions
def get_category_id(category_name):
    """Get the category ID for a given category name, create if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
    result = cursor.fetchone()
    
    if result:
        conn.close()
        return result[0]
    
    # Create the category if it doesn't exist
    cursor.execute('INSERT INTO categories (name) VALUES (?)', (category_name,))
    category_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return category_id

def get_category_name(category_id):
    """Get the category name for a given category ID."""
    if category_id is None:
        return "None"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT name FROM categories WHERE id = ?', (category_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    return "Unknown"

def format_due_date(due_date):
    """Format the due date for display."""
    if due_date is None:
        return ""
    
    try:
        date_obj = datetime.datetime.fromisoformat(due_date)
        return date_obj.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return due_date

# Command implementations
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
    
    # Parse due date if provided
    due_date = None
    if due:
        try:
            due_date = date_parse(due).isoformat()
        except ValueError:
            typer.echo("Invalid date format. Please use YYYY-MM-DD.")
            raise typer.Exit(1)
    
    # Get or create category
    category_id = get_category_id(category)
    
    # Insert todo
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        'INSERT INTO todos (message, priority, category_id, due_date) VALUES (?, ?, ?, ?)',
        (message, priority, category_id, due_date)
    )
    
    todo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    typer.echo(f"Added todo #{todo_id}: {message}")

@app.command("ac")
def add_category(name: str):
    """Add a new category."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
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
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if todo exists
    cursor.execute('SELECT * FROM todos WHERE id = ?', (id,))
    todo = cursor.fetchone()
    
    if not todo:
        typer.echo(f"Todo #{id} not found")
        conn.close()
        raise typer.Exit(1)
    
    # Build update query dynamically
    updates = []
    values = []
    
    if message is not None:
        updates.append("message = ?")
        values.append(message)
    
    if priority is not None:
        if priority < 0 or priority > 3:
            typer.echo("Priority must be between 0 and 3")
            conn.close()
            raise typer.Exit(1)
        updates.append("priority = ?")
        values.append(priority)
    
    if category is not None:
        category_id = get_category_id(category)
        updates.append("category_id = ?")
        values.append(category_id)
    
    if due is not None:
        if due.lower() == "none":
            updates.append("due_date = NULL")
        else:
            try:
                due_date = date_parse(due).isoformat()
                updates.append("due_date = ?")
                values.append(due_date)
            except ValueError:
                typer.echo("Invalid date format. Please use YYYY-MM-DD.")
                conn.close()
                raise typer.Exit(1)
    
    if not updates:
        typer.echo("No changes specified")
        conn.close()
        raise typer.Exit(1)
    
    # Execute update
    query = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
    values.append(id)
    
    cursor.execute(query, values)
    conn.commit()
    
    # Get updated todo
    cursor.execute('SELECT id, message, priority, category_id, due_date FROM todos WHERE id = ?', (id,))
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
    
    # Check if category exists
    cursor.execute('SELECT * FROM categories WHERE id = ?', (id,))
    category = cursor.fetchone()
    
    if not category:
        typer.echo(f"Category #{id} not found")
        conn.close()
        raise typer.Exit(1)
    
    # Update category
    try:
        cursor.execute('UPDATE categories SET name = ? WHERE id = ?', (name, id))
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
):
    """List todos with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query with filters
    query = '''
    SELECT t.id, t.message, t.priority, c.name, t.completed, t.due_date
    FROM todos t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE 1=1
    '''
    params = []
    
    if priority is not None:
        query += " AND t.priority = ?"
        params.append(priority)
    
    if category is not None:
        query += " AND c.name = ?"
        params.append(category)
    
    if done:
        query += " AND t.completed = 1"
    
    if undone:
        query += " AND t.completed = 0"
    
    if overdue:
        today = datetime.datetime.now().date().isoformat()
        query += " AND t.due_date < ? AND t.completed = 0"
        params.append(today)
    
    # Order by
    if due:
        query += " ORDER BY t.due_date, t.priority DESC"
    else:
        query += " ORDER BY t.priority DESC, t.id"
    
    cursor.execute(query, params)
    todos = cursor.fetchall()
    conn.close()
    
    if not todos:
        typer.echo("No todos found matching criteria")
        return
    
    # Create rich table for output
    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="bold")
    table.add_column("Message")
    table.add_column("Priority", style="bold")
    table.add_column("Category")
    table.add_column("Due Date")
    table.add_column("Status")
    
    for todo in todos:
        todo_id, message, priority, category_name, completed, due_date = todo
        
        if category_name is None:
            category_name = "General"
        
        priority_name, priority_color = PRIORITIES[priority]
        priority_text = Text(priority_name, style=priority_color)
        id_text = Text(str(todo_id), style=priority_color)
        
        status = "✓" if completed else " "
        
        due_date_str = format_due_date(due_date)
        
        # Check if overdue
        due_style = ""
        if due_date and not completed:
            try:
                due_date_obj = datetime.datetime.fromisoformat(due_date).date()
                today = datetime.datetime.now().date()
                if due_date_obj < today:
                    due_style = "red bold"
            except (ValueError, TypeError):
                pass
        
        due_text = Text(due_date_str, style=due_style) if due_style else due_date_str
        
        table.add_row(
            id_text,
            message,
            priority_text,
            category_name,
            due_text,
            status
        )
    
    console.print(table)

@app.command("lc")
def list_categories():
    """List all categories."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT c.id, c.name, COUNT(t.id) as todo_count
    FROM categories c
    LEFT JOIN todos t ON c.id = t.category_id
    GROUP BY c.id
    ORDER BY c.name
    ''')
    
    categories = cursor.fetchall()
    conn.close()
    
    if not categories:
        typer.echo("No categories found")
        return
    
    # Create rich table for output
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
    
    cursor.execute('UPDATE todos SET completed = 1 WHERE id = ?', (id,))
    
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
    
    cursor.execute('UPDATE todos SET completed = 0 WHERE id = ?', (id,))
    
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
    
    # First remove any notes
    cursor.execute('DELETE FROM notes WHERE todo_id = ?', (id,))
    
    # Then remove the todo
    cursor.execute('DELETE FROM todos WHERE id = ?', (id,))
    
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
    
    # First set any todos in this category to the default category
    cursor.execute('UPDATE todos SET category_id = 1 WHERE category_id = ?', (id,))
    
    # Then remove the category
    cursor.execute('DELETE FROM categories WHERE id = ?', (id,))
    
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
    
    # Check if todo exists
    cursor.execute('SELECT * FROM todos WHERE id = ?', (id,))
    todo = cursor.fetchone()
    
    if not todo:
        typer.echo(f"Todo #{id} not found")
        conn.close()
        raise typer.Exit(1)
    
    # Add note
    cursor.execute('INSERT INTO notes (todo_id, content) VALUES (?, ?)', (id, content))
    note_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    typer.echo(f"Added note #{note_id} to todo #{id}")

@app.command("ln")
def list_notes(id: int):
    """List notes for a todo."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if todo exists
    cursor.execute('SELECT message FROM todos WHERE id = ?', (id,))
    todo = cursor.fetchone()
    
    if not todo:
        typer.echo(f"Todo #{id} not found")
        conn.close()
        raise typer.Exit(1)
    
    # Get notes
    cursor.execute('''
    SELECT id, content, created_at
    FROM notes
    WHERE todo_id = ?
    ORDER BY created_at
    ''', (id,))
    
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
        note_id, content, created_at = note
        table.add_row(str(note_id), content, created_at)
    
    console.print(table)

@app.command("search")
def search(keyword: str):
    """Search todos by keyword."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT t.id, t.message, t.priority, c.name, t.completed, t.due_date
    FROM todos t
    LEFT JOIN categories c ON t.category_id = c.id
    WHERE t.message LIKE ? OR c.name LIKE ?
    ORDER BY t.priority DESC, t.id
    ''', (f'%{keyword}%', f'%{keyword}%'))
    
    todos = cursor.fetchall()
    conn.close()
    
    if not todos:
        typer.echo(f"No todos found matching '{keyword}'")
        return
    
    # Create rich table for output
    table = Table(show_header=True)
    table.add_column("ID")
    table.add_column("Message")
    table.add_column("Priority")
    table.add_column("Category")
    table.add_column("Due Date")
    table.add_column("Status")
    
    for todo in todos:
        todo_id, message, priority, category_name, completed, due_date = todo
        
        if category_name is None:
            category_name = "General"
        
        priority_name, priority_color = PRIORITIES[priority]
        priority_text = Text(priority_name, style=priority_color)
        
        status = "✓" if completed else " "
        
        due_date_str = format_due_date(due_date)
        
        table.add_row(
            Text(str(todo_id), style=priority_color),
            message,
            priority_text,
            Text(category_name, style=priority_color),
            Text(due_date_str, style=priority_color),
            Text(status, style=priority_color)
        )
    
    console.print(table)

@app.command("export")
def export_todos(filename: str):
    """Export todos to a CSV file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT t.id, t.message, t.priority, c.name, t.completed, t.due_date
    FROM todos t
    LEFT JOIN categories c ON t.category_id = c.id
    ORDER BY t.id
    ''')
    
    todos = cursor.fetchall()
    conn.close()
    
    if not todos:
        typer.echo("No todos to export")
        return
    
    # Write to CSV
    import csv
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Message', 'Priority', 'Category', 'Completed', 'Due Date'])
        writer.writerows(todos)
    
    typer.echo(f"Exported {len(todos)} todos to {filename}")

@app.command("import")
def import_todos(filename: str):
    """Import todos from a CSV file."""
    import csv
    
    try:
        with open(filename, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header
            
            # Validate header
            expected_header = ['ID', 'Message', 'Priority', 'Category', 'Completed', 'Due Date']
            if header != expected_header:
                typer.echo(f"Invalid CSV format. Expected header: {', '.join(expected_header)}")
                return
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            imported = 0
            for row in reader:
                if len(row) != 6:
                    continue
                
                _, message, priority, category, completed, due_date = row
                
                # Get or create category
                category_id = get_category_id(category)
                
                # Validate priority
                try:
                    priority = int(priority)
                    if priority < 0 or priority > 3:
                        priority = 0
                except ValueError:
                    priority = 0
                
                # Validate completed
                completed = 1 if completed == '1' else 0
                
                # Validate due date
                if due_date == 'None' or due_date == '':
                    due_date = None
                
                # Insert todo
                cursor.execute(
                    'INSERT INTO todos (message, priority, category_id, completed, due_date) VALUES (?, ?, ?, ?, ?)',
                    (message, priority, category_id, completed, due_date)
                )
                
                imported += 1
            
            conn.commit()
            conn.close()
            
            typer.echo(f"Imported {imported} todos")
    
    except FileNotFoundError:
        typer.echo(f"File {filename} not found")
    except Exception as e:
        typer.echo(f"Error importing todos: {e}")

@app.command("stats")
def show_stats():
    """Show statistics about todos."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total todos
    cursor.execute('SELECT COUNT(*) FROM todos')
    total = cursor.fetchone()[0]
    
    # Completed todos
    cursor.execute('SELECT COUNT(*) FROM todos WHERE completed = 1')
    completed = cursor.fetchone()[0]
    
    # Incomplete todos
    incomplete = total - completed
    
    # Overdue todos
    today = datetime.datetime.now().date().isoformat()
    cursor.execute('SELECT COUNT(*) FROM todos WHERE due_date < ? AND completed = 0', (today,))
    overdue = cursor.fetchone()[0]
    
    # Todos by priority
    cursor.execute('''
    SELECT priority, COUNT(*)
    FROM todos
    GROUP BY priority
    ORDER BY priority
    ''')
    priority_counts = cursor.fetchall()
    
    # Todos by category
    cursor.execute('''
    SELECT c.name, COUNT(t.id)
    FROM categories c
    LEFT JOIN todos t ON c.id = t.category_id
    GROUP BY c.id
    ORDER BY COUNT(t.id) DESC
    ''')
    category_counts = cursor.fetchall()
    
    conn.close()
    
    # Display statistics
    typer.echo(f"Total todos: {total}")
    typer.echo(f"Completed: {completed}")
    typer.echo(f"Incomplete: {incomplete}")
    typer.echo(f"Overdue: {overdue}")
    
    typer.echo("\nTodos by priority:")
    for priority, count in priority_counts:
        priority_name, priority_color = PRIORITIES[priority]
        text = Text(f"{priority_name}: {count}", style=priority_color)
        console.print(text)
    
    typer.echo("\nTodos by category:")
    for category, count in category_counts:
        typer.echo(f"{category}: {count}")

@app.command("init")
def init():
    """Initialize the database and set up the application."""
    init_db()
    typer.echo("Database initialized successfully!")
    typer.echo("Application is ready to use!")

def main():
    app()

if __name__ == "__main__":
    main()
