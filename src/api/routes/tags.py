from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import TagOut
from src.services import tags as tags_svc

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagOut])
def list_all_tags():
    return [
        TagOut(id=t.id, name=t.name, todo_count=t.todo_count) for t in tags_svc.list_tags()
    ]
