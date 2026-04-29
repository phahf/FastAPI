import pytest
from fastapi.testclient import TestClient
from app.main import app, get_user_service
from tests.fakes import FakeUserService



@pytest.fixture
def fake_user_service():
    return FakeUserService()

@pytest.fixture
def client(fake_user_service):
    app.dependency_overrides[get_user_service] = lambda: fake_user_service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

## Happy Path tests

def test_api_get_users_happy_path(client):
    response = client.get("/users")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_create_user_happy_path(client):
    response = client.post(
        "/users",
        json={
            "username": "happyuser",
            "password": "ValidPass123"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == "happyuser"


def test_api_get_user_by_id_happy_path(client):
    create = client.post(
        "/users",
        json={
            "username": "singleuser",
            "password": "ValidPass123"
        }
    )
    user_id = create.json()["id"]
    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["username"] == "singleuser"


def test_api_change_password_happy_path(client):
    create = client.post(
        "/users",
        json={
            "username": "pwuser",
            "password": "OldPass123"
        }
    )
    user_id = create.json()["id"]
    response = client.patch(
        f"/users/{user_id}/password",
        json={
            "current_password": "OldPass123",
            "new_password": "NewPass123"
        }
    )

    assert response.status_code == 204


def test_api_delete_user_happy_path(client):
    create = client.post(
        "/users",
        json={
            "username": "deleteuser",
            "password": "ValidPass123"
        }
    )
    user_id = create.json()["id"]
    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 204



## Fehlerfälle testen

## Enthält Business Logik
# def test_api_create_user_invalid_password():
#     response = client.post(
#         "/users",
#         json={
#             "username": "badpassworduser",
#             "password": "short"
#         }
#     )

#     assert response.status_code == 400
#     assert "Password" in response.json()["detail"]


## Enthält Business Logik
# def test_api_create_user_username_already_exists():
#     client.post(
#         "/users",
#         json={
#             "username": "duplicateuser",
#             "password": "ValidPass123"
#         }
#     )

#     response = client.post(
#         "/users",
#         json={
#             "username": "duplicateuser",
#             "password": "ValidPass123"
#         }
#     )

#     assert response.status_code == 409


def test_api_get_user_not_found(client):
    response = client.get("/users/999999")

    assert response.status_code == 404


def test_api_change_password_user_not_found(client):
    response = client.patch(
        "/users/999999/password",
        json={
            "current_password": "Whatever123",
            "new_password": "NewValid123"
        }
    )

    assert response.status_code == 404


## Enthält Business Logik
# def test_api_change_password_invalid_current_password():
#     create = client.post(
#         "/users",
#         json={
#             "username": "wrongpwuser1",
#             "password": "Correct123"
#         }
#     )
#     user_id = create.json()["id"]

#     response = client.patch(
#         f"/users/{user_id}/password",
#         json={
#             "current_password": "Wrong123",
#             "new_password": "NewCorrect123"
#         }
#     )

#     assert response.status_code == 401


