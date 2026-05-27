import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import TodoCreate
from tests.utils.todo import create_random_todo
from tests.utils.user import create_random_user, user_authentication_headers
from tests.utils.utils import random_lower_string


def _current_user_id(client: TestClient, headers: dict[str, str]) -> str:
    return client.get(f"{settings.API_V1_STR}/users/me", headers=headers).json()["id"]


def test_create_todo(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    data = {"title": "Buy milk", "description": "2L oat milk"}
    r = client.post(
        f"{settings.API_V1_STR}/todos/", headers=normal_user_token_headers, json=data
    )
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == data["title"]
    assert body["description"] == data["description"]
    assert body["is_completed"] is False
    assert "id" in body
    assert body["owner_id"] == _current_user_id(client, normal_user_token_headers)


def test_create_todo_title_required(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/todos/",
        headers=normal_user_token_headers,
        json={"title": ""},
    )
    assert r.status_code == 422


def test_read_todo(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    me_id = _current_user_id(client, normal_user_token_headers)
    todo = crud.todo.create(
        session=db,
        todo_in=TodoCreate(title=random_lower_string(10)),
        owner_id=uuid.UUID(me_id),
    )
    r = client.get(
        f"{settings.API_V1_STR}/todos/{todo.id}", headers=normal_user_token_headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == str(todo.id)
    assert body["title"] == todo.title


def test_read_todo_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/todos/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404
    assert r.json()["detail"] == "Todo not found"


def test_read_todo_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    other_todo = create_random_todo(db)
    r = client.get(
        f"{settings.API_V1_STR}/todos/{other_todo.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Not enough privileges"


def test_list_todos_only_returns_own(
    client: TestClient,
    db: Session,
) -> None:
    user_a, pwd_a = create_random_user(db)
    user_b, _ = create_random_user(db)
    crud.todo.create(session=db, todo_in=TodoCreate(title="a1"), owner_id=user_a.id)
    crud.todo.create(session=db, todo_in=TodoCreate(title="a2"), owner_id=user_a.id)
    crud.todo.create(session=db, todo_in=TodoCreate(title="b1"), owner_id=user_b.id)

    headers = user_authentication_headers(
        client=client, email=user_a.email, password=pwd_a
    )
    r = client.get(f"{settings.API_V1_STR}/todos/", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert len(body["data"]) == 2
    assert all(t["owner_id"] == str(user_a.id) for t in body["data"])


def test_list_todos_pagination(
    client: TestClient,
    db: Session,
) -> None:
    user, password = create_random_user(db)
    for i in range(3):
        crud.todo.create(
            session=db, todo_in=TodoCreate(title=f"t{i}"), owner_id=user.id
        )
    headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    r = client.get(f"{settings.API_V1_STR}/todos/?skip=1&limit=1", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 3
    assert len(body["data"]) == 1


def test_update_todo(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    me_id = _current_user_id(client, normal_user_token_headers)
    todo = crud.todo.create(
        session=db,
        todo_in=TodoCreate(title="not done yet"),
        owner_id=uuid.UUID(me_id),
    )
    r = client.patch(
        f"{settings.API_V1_STR}/todos/{todo.id}",
        headers=normal_user_token_headers,
        json={"is_completed": True},
    )
    assert r.status_code == 200
    assert r.json()["is_completed"] is True


def test_update_todo_partial(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    me_id = _current_user_id(client, normal_user_token_headers)
    todo = crud.todo.create(
        session=db,
        todo_in=TodoCreate(title="keep title", description="old desc"),
        owner_id=uuid.UUID(me_id),
    )
    r = client.patch(
        f"{settings.API_V1_STR}/todos/{todo.id}",
        headers=normal_user_token_headers,
        json={"description": "new desc"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "keep title"
    assert body["description"] == "new desc"
    assert body["is_completed"] is False


def test_update_todo_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.patch(
        f"{settings.API_V1_STR}/todos/{uuid.uuid4()}",
        headers=normal_user_token_headers,
        json={"title": "anything"},
    )
    assert r.status_code == 404


def test_update_todo_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    other_todo = create_random_todo(db)
    r = client.patch(
        f"{settings.API_V1_STR}/todos/{other_todo.id}",
        headers=normal_user_token_headers,
        json={"title": "stolen"},
    )
    assert r.status_code == 403


def test_delete_todo(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    me_id = _current_user_id(client, normal_user_token_headers)
    todo = crud.todo.create(
        session=db,
        todo_in=TodoCreate(title="to delete"),
        owner_id=uuid.UUID(me_id),
    )
    r = client.delete(
        f"{settings.API_V1_STR}/todos/{todo.id}", headers=normal_user_token_headers
    )
    assert r.status_code == 200
    assert r.json()["message"] == "Todo deleted"
    follow_up = client.get(
        f"{settings.API_V1_STR}/todos/{todo.id}", headers=normal_user_token_headers
    )
    assert follow_up.status_code == 404


def test_delete_todo_not_found(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.delete(
        f"{settings.API_V1_STR}/todos/{uuid.uuid4()}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 404


def test_delete_todo_not_enough_permissions(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    other_todo = create_random_todo(db)
    r = client.delete(
        f"{settings.API_V1_STR}/todos/{other_todo.id}",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 403
