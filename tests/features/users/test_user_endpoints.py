"""User management endpoint tests."""

from __future__ import annotations

import uuid

from tests.factories import DEFAULT_PASSWORD, create_user
from tests.helpers import assert_error, assert_page


async def test_list_users(client) -> None:
    """Staff can list users with pagination metadata."""
    response = await client.get("/v1/user/", params={"page": 1, "size": 5})
    assert response.status_code == 200
    items = assert_page(response.json(), page=1, size=5)
    assert any(item["full_name"] == "Staff User" for item in items)


async def test_get_user_success_and_not_found(client, session) -> None:
    """Staff can fetch a user by id."""
    user = await create_user(session, full_name="Lookup User")

    found = await client.get(f"/v1/user/{user.id}")
    assert found.status_code == 200
    assert found.json()["id"] == str(user.id)

    missing = await client.get(f"/v1/user/{uuid.uuid4()}")
    assert_error(missing, 404, "User not found")


async def test_create_user(client) -> None:
    """Staff can create users."""
    response = await client.post(
        "/v1/user/",
        json={
            "email": "created@example.com",
            "phone": "0912345678",
            "password": DEFAULT_PASSWORD,
            "full_name": "Created User",
            "role": "CUSTOMER",
            "is_active": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["email"] == "created@example.com"
    assert response.json()["phone"] == "+84912345678"


async def test_update_user(client, session) -> None:
    """Staff can update mutable user fields."""
    user = await create_user(session, full_name="Before Update")

    response = await client.patch(f"/v1/user/{user.id}", json={"full_name": "After Update", "is_active": False})
    assert response.status_code == 200
    assert response.json()["full_name"] == "After Update"
    assert response.json()["is_active"] is False

    missing = await client.patch(f"/v1/user/{uuid.uuid4()}", json={"full_name": "Nobody"})
    assert_error(missing, 404, "User not found")


async def test_change_password(client, session) -> None:
    """Staff can change a user password."""
    user = await create_user(session)

    response = await client.post(
        f"/v1/user/{user.id}/change-password",
        json={"current_password": DEFAULT_PASSWORD, "new_password": "NewPassword123"},
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Password changed"}

    wrong = await client.post(
        f"/v1/user/{user.id}/change-password",
        json={"current_password": "WrongPassword", "new_password": "AnotherPassword123"},
    )
    assert_error(wrong, 400, "Current password is incorrect")
