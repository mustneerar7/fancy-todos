import uuid

from sqlmodel import Session

from app import crud
from app.models import TodoCreate, TodoUpdate
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def test_create_todo_sets_owner_id(db: Session) -> None:
    user, _ = create_random_user(db)
    todo = crud.todo.create(
        session=db,
        todo_in=TodoCreate(title=random_lower_string(10)),
        owner_id=user.id,
    )
    assert todo.owner_id == user.id
    assert todo.id is not None
    assert todo.is_completed is False


def test_get_todo_returns_none_for_missing(db: Session) -> None:
    assert crud.todo.get(session=db, todo_id=uuid.uuid4()) is None


def test_get_multi_by_owner_filters(db: Session) -> None:
    a, _ = create_random_user(db)
    b, _ = create_random_user(db)
    for _ in range(2):
        crud.todo.create(session=db, todo_in=TodoCreate(title="a"), owner_id=a.id)
    crud.todo.create(session=db, todo_in=TodoCreate(title="b"), owner_id=b.id)

    items, count = crud.todo.get_multi_by_owner(session=db, owner_id=a.id)
    assert count == 2
    assert len(items) == 2
    assert all(t.owner_id == a.id for t in items)


def test_get_multi_by_owner_pagination(db: Session) -> None:
    user, _ = create_random_user(db)
    for i in range(3):
        crud.todo.create(
            session=db, todo_in=TodoCreate(title=f"t{i}"), owner_id=user.id
        )
    items, count = crud.todo.get_multi_by_owner(
        session=db, owner_id=user.id, skip=1, limit=1
    )
    assert count == 3
    assert len(items) == 1


def test_update_todo_partial(db: Session) -> None:
    user, _ = create_random_user(db)
    todo = crud.todo.create(
        session=db,
        todo_in=TodoCreate(title="original", description="original desc"),
        owner_id=user.id,
    )
    updated = crud.todo.update(
        session=db, db_todo=todo, todo_in=TodoUpdate(is_completed=True)
    )
    assert updated.title == "original"
    assert updated.description == "original desc"
    assert updated.is_completed is True
