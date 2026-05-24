import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import Session

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import Message, Todo, TodoCreate, TodoPublic, TodosPublic, TodoUpdate, User

router = APIRouter(prefix="/todos", tags=["todos"])


def _get_owned(session: Session, current_user: User, todo_id: uuid.UUID) -> Todo:
    todo = crud.todo.get(session=session, todo_id=todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    if todo.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return todo


@router.get("/", response_model=TodosPublic)
def list_todos(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
):
    items, count = crud.todo.get_multi_by_owner(
        session=session, owner_id=current_user.id, skip=skip, limit=limit
    )
    return TodosPublic(data=items, count=count)


@router.post("/", response_model=TodoPublic)
def create_todo(*, session: SessionDep, current_user: CurrentUser, todo_in: TodoCreate):
    return crud.todo.create(session=session, todo_in=todo_in, owner_id=current_user.id)


@router.get("/{todo_id}", response_model=TodoPublic)
def read_todo(todo_id: uuid.UUID, session: SessionDep, current_user: CurrentUser):
    return _get_owned(session, current_user, todo_id)


@router.patch("/{todo_id}", response_model=TodoPublic)
def update_todo(
    *,
    todo_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    todo_in: TodoUpdate,
):
    db_todo = _get_owned(session, current_user, todo_id)
    return crud.todo.update(session=session, db_todo=db_todo, todo_in=todo_in)


@router.delete("/{todo_id}", response_model=Message)
def delete_todo(todo_id: uuid.UUID, session: SessionDep, current_user: CurrentUser):
    db_todo = _get_owned(session, current_user, todo_id)
    crud.todo.delete(session=session, db_todo=db_todo)
    return Message(message="Todo deleted")
