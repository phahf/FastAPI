import pytest
from app.service import UserService
from app.exceptions import (
    UserAlreadyExists,
    UserNotFound,
    InvalidPassword,
    InvalidCurrentPassword
)
from sqlmodel import create_engine
from app.db.engine import create_db_and_tables, get_session


# Fixture: Session und UserService für die Tests
@pytest.fixture
def test_session():
    test_engine = create_engine("sqlite:///:memory:")
    create_db_and_tables(test_engine)
    session = get_session(test_engine)
    yield session
    session.close()

@pytest.fixture
def test_service(test_session):
    return UserService(test_session)



def test_userservice_create_user_happy_path(test_service):
    user = test_service.create_user("alice", "ValidPass123")

    assert user["username"] == "alice"
    assert "id" in user



def test_userservice_get_user_by_id_happy_path(test_service):
    created = test_service.create_user("alice", "ValidPass123")
    user = test_service.get_user_by_id(created["id"])

    assert user["id"] == created["id"]
    assert user["username"] == "alice"


def test_userservice_duplicate_username_raises(test_service):
    test_service.create_user("bob", "ValidPass123")

    with pytest.raises(UserAlreadyExists):
        test_service.create_user("bob", "ValidPass123")


def test_userservice_invalid_password_raises(test_service):
    with pytest.raises(InvalidPassword):
        test_service.create_user("charlie", "short")


def test_userservice_user_not_found_raises(test_service):
    with pytest.raises(UserNotFound):
        test_service.get_user_by_id(999)


def test_userservice_change_password_happy_path(test_service):
    user = test_service.create_user("dave", "OldPass123")

    test_service.change_password(
        user_id=user["id"],
        current_password="OldPass123",
        new_password="NewPass123"
    )


def test_userservice_change_password_invalid_current_password(test_service):
    user = test_service.create_user("erin", "Correct123")

    with pytest.raises(InvalidCurrentPassword):
        test_service.change_password(
            user_id=user["id"],
            current_password="Wrong123",
            new_password="NewCorrect123"
        )



def test_userservice_delete_user_happy_path(test_service):
    user = test_service.create_user("frank", "ValidPass123")
    test_service.delete_user(user["id"])

    with pytest.raises(UserNotFound):
        test_service.get_user_by_id(user["id"])


def test_userservice_delete_user_not_found(test_service):
    with pytest.raises(UserNotFound):
        test_service.delete_user(999)
