import uuid

from sqlmodel import Session, func, select

from app.models import Todo, TodoCreate, TodoUpdate


def create(*, session: Session, todo_in: TodoCreate, owner_id: uuid.UUID) -> Todo:
    db_obj = Todo.model_validate(todo_in, update={"owner_id": owner_id})
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get(*, session: Session, todo_id: uuid.UUID) -> Todo | None:
    return session.get(Todo, todo_id)


def get_multi_by_owner(
    *, session: Session, owner_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[Todo], int]:
    count = session.exec(
        select(func.count()).select_from(Todo).where(Todo.owner_id == owner_id)
    ).one()
    items = session.exec(
        select(Todo).where(Todo.owner_id == owner_id).offset(skip).limit(limit)
    ).all()
    return list(items), count


def update(*, session: Session, db_todo: Todo, todo_in: TodoUpdate) -> Todo:
    data = todo_in.model_dump(exclude_unset=True)
    db_todo.sqlmodel_update(data)
    session.add(db_todo)
    session.commit()
    session.refresh(db_todo)
    return db_todo


def delete(*, session: Session, db_todo: Todo) -> None:
    session.delete(db_todo)
    session.commit()
