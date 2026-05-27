from sqlmodel import Session

from app import crud
from app.core.security import verify_password
from app.models import UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string


def test_create_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user = crud.user.create(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    assert user.email == email
    assert hasattr(user, "hashed_password")
    assert user.hashed_password != password
    assert verify_password(password, user.hashed_password)


def test_authenticate_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    crud.user.create(session=db, user_create=UserCreate(email=email, password=password))
    authenticated = crud.user.authenticate(session=db, email=email, password=password)
    assert authenticated is not None
    assert authenticated.email == email


def test_not_authenticate_user_wrong_password(db: Session) -> None:
    email = random_email()
    crud.user.create(
        session=db,
        user_create=UserCreate(email=email, password=random_lower_string()),
    )
    assert (
        crud.user.authenticate(session=db, email=email, password="not-the-password")
        is None
    )


def test_not_authenticate_user_missing(db: Session) -> None:
    assert (
        crud.user.authenticate(
            session=db, email=random_email(), password=random_lower_string()
        )
        is None
    )


def test_check_if_user_is_active_default(db: Session) -> None:
    user = crud.user.create(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    assert user.is_active is True


def test_check_if_user_is_superuser_default(db: Session) -> None:
    user = crud.user.create(
        session=db,
        user_create=UserCreate(email=random_email(), password=random_lower_string()),
    )
    assert user.is_superuser is False


def test_get_user_by_email(db: Session) -> None:
    email = random_email()
    crud.user.create(
        session=db,
        user_create=UserCreate(email=email, password=random_lower_string()),
    )
    found = crud.user.get_by_email(session=db, email=email)
    missing = crud.user.get_by_email(session=db, email=random_email())
    assert found is not None
    assert found.email == email
    assert missing is None


def test_update_user_password_rehashes(db: Session) -> None:
    email = random_email()
    user = crud.user.create(
        session=db,
        user_create=UserCreate(email=email, password=random_lower_string()),
    )
    original_hash = user.hashed_password
    new_password = random_lower_string()
    updated = crud.user.update(
        session=db, db_user=user, user_in=UserUpdate(password=new_password)
    )
    assert updated.hashed_password != original_hash
    assert verify_password(new_password, updated.hashed_password)
