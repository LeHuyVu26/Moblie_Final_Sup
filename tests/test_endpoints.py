"""Endpoint smoke tests."""

from httpx import AsyncClient

from app.domain.entities import User
from app.domain.enums import UserRole


async def test_staff_can_list_users(client: AsyncClient, staff_user: User) -> None:
    """Staff role dependency and user response mapper work together."""
    response = await client.get("/v1/user/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == str(staff_user.id)
    assert payload["items"][0]["role"] == UserRole.STAFF.value


async def test_staff_can_get_own_profile(client: AsyncClient, staff_user: User) -> None:
    """Authenticated profile endpoint returns mapped user data."""
    response = await client.get("/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(staff_user.id)
