import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User

__all__ = [
    "Todo",
    "TodoBase",
    "TodoCreate",
    "TodoPublic",
    "TodoUpdate",
    "TodosPublic",
]


class TodoBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_completed: bool = False


class TodoCreate(TodoBase):
    pass


class TodoUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    is_completed: bool | None = None


class Todo(TodoBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    owner: "User" = Relationship(back_populates="todos")


class TodoPublic(TodoBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class TodosPublic(SQLModel):
    data: list[TodoPublic]
    count: int
