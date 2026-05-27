from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string


def user_authentication_headers(
    *, client: TestClient, email: str, password: str
) -> dict[str, str]:
    data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=data)
    response = r.json()
    auth_token = response["access_token"]
    return {"Authorization": f"Bearer {auth_token}"}


def create_random_user(db: Session) -> tuple[User, str]:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.user.create(session=db, user_create=user_in)
    return user, password


def authentication_token_from_email(
    *, client: TestClient, email: str, db: Session
) -> dict[str, str]:
    """Return auth headers for a user with `email`.

    If the user does not exist, it is created. Either way the password is reset
    to a known value so the login call succeeds. This lets tests share a stable
    "normal user" identity across modules without leaking state.
    """
    password = random_lower_string()
    user = crud.user.get_by_email(session=db, email=email)
    if user is None:
        user_in_create = UserCreate(email=email, password=password)
        crud.user.create(session=db, user_create=user_in_create)
    else:
        user_in_update = UserUpdate(password=password)
        crud.user.update(session=db, db_user=user, user_in=user_in_update)
    return user_authentication_headers(client=client, email=email, password=password)
