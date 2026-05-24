from sqlmodel import SQLModel

__all__ = ["Token", "TokenPayload"]


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(SQLModel):
    sub: str | None = None
