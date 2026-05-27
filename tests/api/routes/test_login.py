from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string


def test_get_access_token(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER_EMAIL,
        "password": settings.FIRST_SUPERUSER_PASSWORD,
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    tokens = r.json()
    assert r.status_code == 200
    assert "access_token" in tokens
    assert tokens["access_token"]
    assert tokens["token_type"] == "bearer"


def test_get_access_token_incorrect_password(client: TestClient) -> None:
    login_data = {
        "username": settings.FIRST_SUPERUSER_EMAIL,
        "password": "wrong-password",
    }
    r = client.post(f"{settings.API_V1_STR}/login/access-token", data=login_data)
    assert r.status_code == 400
    assert r.json()["detail"] == "Incorrect email or password"


def test_get_access_token_inactive_user(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.user.create(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    crud.user.update(session=db, db_user=user, user_in=UserUpdate(is_active=False))

    r = client.post(
        f"{settings.API_V1_STR}/login/access-token",
        data={"username": email, "password": password},
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "Inactive user"
