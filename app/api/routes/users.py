import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    Message,
    User,
    UserCreate,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", dependencies=[Depends(get_current_active_superuser)], response_model=UsersPublic)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100):
    count = session.exec(select(func.count()).select_from(User)).one()
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return UsersPublic(data=users, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(*, session: SessionDep, user_in: UserCreate):
    user = crud.user.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    return crud.user.create(session=session, user_create=user_in)


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister):
    user = crud.user.get_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    user_create = UserCreate.model_validate(user_in)
    return crud.user.create(session=session, user_create=user_create)


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser):
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_user_me(*, session: SessionDep, user_in: UserUpdate, current_user: CurrentUser):
    if user_in.email and user_in.email != current_user.email:
        existing = crud.user.get_by_email(session=session, email=user_in.email)
        if existing:
            raise HTTPException(status_code=409, detail="User with this email already exists")
    return crud.user.update(session=session, db_user=current_user, user_in=user_in)


@router.get("/{user_id}", response_model=UserPublic)
def read_user(user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user != current_user and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return user


@router.delete(
    "/{user_id}", dependencies=[Depends(get_current_active_superuser)], response_model=Message
)
def delete_user(session: SessionDep, user_id: uuid.UUID):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return Message(message="User deleted")
