import sqlite3
import pytest

from app.service import UserService
from app.exceptions import (
    UserAlreadyExists,
    UserNotFound,
    InvalidPassword,
    InvalidCurrentPassword
)

# Helper: Datenbank initialisieren
def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    conn.commit()



def test_userservice_create_user_happy_path():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    service = UserService(conn)

    user = service.create_user("alice", "ValidPass123")

    assert user["username"] == "alice"
    assert "id" in user


def test_userservice_duplicate_username_raises():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    service = UserService(conn)

    service.create_user("bob", "ValidPass123")

    with pytest.raises(UserAlreadyExists):
        service.create_user("bob", "ValidPass123")


def test_userservice_invalid_password_raises():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    service = UserService(conn)

    with pytest.raises(InvalidPassword):
        service.create_user("charlie", "short")


def test_userservice_user_not_found_raises():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    service = UserService(conn)

    with pytest.raises(UserNotFound):
        service.get_user_by_id(999)


def test_userservice_change_password_happy_path():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    service = UserService(conn)

    user = service.create_user("dave", "OldPass123")

    service.change_password(
        user_id=user["id"],
        current_password="OldPass123",
        new_password="NewPass123"
    )


def test_userservice_change_password_invalid_current_password():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    service = UserService(conn)

    user = service.create_user("erin", "Correct123")

    with pytest.raises(InvalidCurrentPassword):
        service.change_password(
            user_id=user["id"],
            current_password="Wrong123",
            new_password="NewCorrect123"
        )



def test_userservice_delete_user_happy_path():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    service = UserService(conn)

    user = service.create_user("frank", "ValidPass123")
    service.delete_user(user["id"])

    with pytest.raises(UserNotFound):
        service.get_user_by_id(user["id"])