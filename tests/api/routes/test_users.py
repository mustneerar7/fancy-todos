import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import Todo, TodoCreate, User, UserCreate
from tests.utils.user import create_random_user
from tests.utils.utils import random_email, random_lower_string


def test_get_users_superuser_me(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=superuser_token_headers)
    current_user = r.json()
    assert r.status_code == 200
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is True
    assert current_user["email"] == settings.FIRST_SUPERUSER_EMAIL


def test_get_users_normal_user_me(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers)
    current_user = r.json()
    assert r.status_code == 200
    assert current_user["is_active"] is True
    assert current_user["is_superuser"] is False
    assert current_user["email"] == settings.EMAIL_TEST_USER


def test_create_user_new_email(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    email = random_email()
    password = random_lower_string()
    data = {"email": email, "password": password}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data
    )
    assert r.status_code == 200
    created = r.json()
    user = crud.user.get_by_email(session=db, email=email)
    assert user is not None
    assert user.email == created["email"]


def test_create_user_existing_email(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user, _ = create_random_user(db)
    data = {"email": user.email, "password": random_lower_string()}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=superuser_token_headers, json=data
    )
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"]


def test_create_user_by_normal_user(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"email": random_email(), "password": random_lower_string()}
    r = client.post(
        f"{settings.API_V1_STR}/users/", headers=normal_user_token_headers, json=data
    )
    assert r.status_code == 403


def test_retrieve_users(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    create_random_user(db)
    create_random_user(db)
    r = client.get(f"{settings.API_V1_STR}/users/", headers=superuser_token_headers)
    assert r.status_code == 200
    body = r.json()
    assert "data" in body
    assert "count" in body
    assert isinstance(body["data"], list)
    assert body["count"] >= 2
    assert len(body["data"]) >= 2


def test_get_existing_user_as_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user, _ = create_random_user(db)
    r = client.get(
        f"{settings.API_V1_STR}/users/{user.id}", headers=superuser_token_headers
    )
    assert r.status_code == 200
    assert r.json()["email"] == user.email


def test_get_existing_user_as_self(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
) -> None:
    me = client.get(
        f"{settings.API_V1_STR}/users/me", headers=normal_user_token_headers
    ).json()
    r = client.get(
        f"{settings.API_V1_STR}/users/{me['id']}", headers=normal_user_token_headers
    )
    assert r.status_code == 200
    assert r.json()["id"] == me["id"]


def test_get_existing_user_permissions_error(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    other, _ = create_random_user(db)
    r = client.get(
        f"{settings.API_V1_STR}/users/{other.id}", headers=normal_user_token_headers
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Not enough privileges"


def test_get_non_existing_user(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_register_user_new(client: TestClient, db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    data = {"email": email, "password": password, "full_name": "Jane Tester"}
    r = client.post(f"{settings.API_V1_STR}/users/signup", json=data)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == email
    assert body["is_superuser"] is False
    assert crud.user.get_by_email(session=db, email=email) is not None


def test_register_user_already_exists(client: TestClient, db: Session) -> None:
    user, _ = create_random_user(db)
    data = {"email": user.email, "password": random_lower_string()}
    r = client.post(f"{settings.API_V1_STR}/users/signup", json=data)
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"]


def test_update_user_me(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    new_name = "Updated Name"
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"full_name": new_name},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == new_name
    user = crud.user.get_by_email(session=db, email=settings.EMAIL_TEST_USER)
    assert user is not None
    db.refresh(user)
    assert user.full_name == new_name


def test_update_user_me_email_exists(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    other, _ = create_random_user(db)
    r = client.patch(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers,
        json={"email": other.email},
    )
    assert r.status_code == 409


def test_delete_user_superuser(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user, _ = create_random_user(db)
    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}", headers=superuser_token_headers
    )
    assert r.status_code == 200
    assert r.json()["message"] == "User deleted"
    db.expire_all()
    assert db.get(User, user.id) is None


def test_delete_user_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


def test_delete_user_by_normal_user(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    other, _ = create_random_user(db)
    r = client.delete(
        f"{settings.API_V1_STR}/users/{other.id}", headers=normal_user_token_headers
    )
    assert r.status_code == 403


def test_delete_user_cascades_todos(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = crud.user.create(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    crud.todo.create(
        session=db,
        todo_in=TodoCreate(title="will be orphaned"),
        owner_id=user.id,
    )
    r = client.delete(
        f"{settings.API_V1_STR}/users/{user.id}", headers=superuser_token_headers
    )
    assert r.status_code == 200
    db.expire_all()
    remaining = db.exec(select(Todo).where(Todo.owner_id == user.id)).all()
    assert remaining == []
