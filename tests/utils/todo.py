from sqlmodel import Session

from app import crud
from app.models import Todo, TodoCreate, User
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


def create_random_todo(db: Session, *, owner: User | None = None) -> Todo:
    if owner is None:
        owner, _ = create_random_user(db)
    todo_in = TodoCreate(
        title=random_lower_string(20),
        description=random_lower_string(40),
    )
    return crud.todo.create(session=db, todo_in=todo_in, owner_id=owner.id)
