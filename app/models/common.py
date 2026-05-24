from sqlmodel import SQLModel

__all__ = ["Message"]


class Message(SQLModel):
    message: str
