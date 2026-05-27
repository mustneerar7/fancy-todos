from sqlmodel import Session, func, select

from app.core.config import settings
from app.core.db import init_db
from app.models import User


def test_init_db_seeds_first_superuser(db: Session) -> None:
    """The first call to ``init_db`` happens inside the autouse session fixture
    against a freshly-created test database. This assertion verifies that
    branch produced the expected superuser, so the seed is exercised end-to-end
    once per test run."""
    user = db.exec(
        select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
    ).first()
    assert user is not None
    assert user.is_superuser is True
    assert user.is_active is True


def test_init_db_is_idempotent(db: Session) -> None:
    """Calling ``init_db`` again must NOT create a duplicate superuser. This
    matters because the seed runs on every app boot via ``scripts/prestart.sh``
    — a non-idempotent seed would crash on the unique-email constraint after
    the first deploy."""
    init_db(db)
    init_db(db)
    count = db.exec(
        select(func.count())
        .select_from(User)
        .where(User.email == settings.FIRST_SUPERUSER_EMAIL)
    ).one()
    assert count == 1
