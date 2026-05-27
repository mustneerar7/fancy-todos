"""Global pytest fixtures.

The first thing this module does is force ``POSTGRES_DB`` to a `_test` suffix
*before* any ``app.*`` modules import. ``app/core/db.py`` builds its engine at
import time from settings, so the override has to happen at the top of the
import order — otherwise tests would talk to the dev database.
"""

import os

from dotenv import dotenv_values

_env = {**dotenv_values(".env"), **os.environ}
_dev_db = _env.get("POSTGRES_DB", "app")
if not _dev_db.endswith("_test"):
    os.environ["POSTGRES_DB"] = f"{_dev_db}_test"

# ruff: noqa: E402 — imports below must come after the env override above.
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import Engine, create_engine
from sqlmodel import Session, SQLModel, delete

from app.api.deps import get_db
from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Todo, User
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


def _ensure_test_database_exists() -> None:
    """Create the test database if it doesn't exist.

    Connects to the default ``postgres`` maintenance DB to issue the
    ``CREATE DATABASE`` — Postgres won't let you create a DB from a
    connection that's inside another DB.
    """
    admin_url = str(settings.SQLALCHEMY_DATABASE_URI).rsplit("/", 1)[0] + "/postgres"
    admin_engine: Engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    target = settings.POSTGRES_DB
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": target},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{target}"'))
    admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    _ensure_test_database_exists()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        init_db(session)
        yield session
        # Session-end cleanup: wipe data so the next run starts from a known
        # state. Todos first to satisfy the FK to user.
        session.exec(delete(Todo))
        session.exec(delete(User))
        session.commit()


@pytest.fixture(scope="module")
def client(db: Session) -> Generator[TestClient, None, None]:
    """A TestClient whose ``get_db`` dependency yields the shared test session.

    Module scope matches the upstream template: one client per test file keeps
    tests fast without leaking state, since the DB is shared across the session.
    """

    def _get_db_override() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
