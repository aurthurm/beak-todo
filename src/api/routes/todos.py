from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.schemas import NoteCreate, ReorderRequest, TodoCreate, TodoOut, TodoPatch
from src.services import notes as notes_svc
from src.services.todos import (
    ListFilters,
    TodoRecord,
    create_todo,
    delete_todo,
    fetch_by_date_range,
    fetch_by_due_date,
    fetch_inbox,
    get_todo_by_id,
    query_todos,
    reorder_todos,
    update_todo,
    validate_due_date,
)

router = APIRouter(prefix="/todos", tags=["todos"])


def _out(r: TodoRecord) -> TodoOut:
    return TodoOut(
        id=r.id,
        message=r.message,
        priority=r.priority,
        priority_label=r.priority_label,
        priority_color=r.priority_color,
        category=r.category,
        completed=r.completed,
        due_date=r.due_date,
        sort_order=r.sort_order,
    )


@router.get("", response_model=list[TodoOut])
def list_todos(
    due_date: Optional[str] = None,
    due_from: Optional[str] = None,
    due_to: Optional[str] = None,
    completed: Optional[bool] = None,
    category: Optional[str] = None,
    inbox: bool = False,
    search: Optional[str] = None,
    overdue: bool = False,
):
    if inbox:
        return [_out(r) for r in fetch_inbox()]
    if due_date:
        return [_out(r) for r in fetch_by_due_date(due_date)]
    if due_from and due_to:
        inc = completed is True
        return [_out(r) for r in fetch_by_date_range(due_from, due_to, include_completed=inc)]

    f = ListFilters(category=category, search=search, overdue=overdue)
    if completed is True:
        f.done = True
    elif completed is False:
        f.undone = True
    return [_out(r) for r in query_todos(f)]


@router.post("/reorder")
def reorder(body: ReorderRequest):
    reorder_todos([(i.id, i.sort_order) for i in body.items])
    return {"ok": True}


@router.get("/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int):
    r = get_todo_by_id(todo_id)
    if not r:
        raise HTTPException(404, "Todo not found")
    return _out(r)


@router.post("", response_model=TodoOut, status_code=201)
def create(body: TodoCreate):
    due = None
    if body.due_date:
        due = validate_due_date(body.due_date)
    tid = create_todo(body.message, body.priority, body.category, due)
    r = get_todo_by_id(tid)
    return _out(r)


@router.patch("/{todo_id}", response_model=TodoOut)
def patch_todo(todo_id: int, body: TodoPatch):
    due = body.due_date
    if due and not body.clear_due:
        due = validate_due_date(due, body.completed or False)
    ok = update_todo(
        todo_id,
        message=body.message,
        priority=body.priority,
        category=body.category,
        due=due,
        clear_due=body.clear_due,
        completed=body.completed,
        sort_order=body.sort_order,
    )
    if not ok:
        raise HTTPException(404, "Todo not found")
    r = get_todo_by_id(todo_id)
    return _out(r)


@router.delete("/{todo_id}", status_code=204)
def remove(todo_id: int):
    if not delete_todo(todo_id):
        raise HTTPException(404, "Todo not found")


@router.get("/{todo_id}/notes")
def get_notes(todo_id: int):
    if not get_todo_by_id(todo_id):
        raise HTTPException(404, "Todo not found")
    return notes_svc.list_notes(todo_id)


@router.post("/{todo_id}/notes", status_code=201)
def post_note(todo_id: int, body: NoteCreate):
    if not get_todo_by_id(todo_id):
        raise HTTPException(404, "Todo not found")
    nid = notes_svc.add_note(todo_id, body.content)
    return {"id": nid}
