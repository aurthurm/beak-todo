from fastapi import APIRouter

from src.api.schemas import CategoryOut
from src.services.categories import list_categories

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryOut])
def list_all():
    return [
        CategoryOut(id=c.id, name=c.name, todo_count=c.todo_count)
        for c in list_categories()
    ]
