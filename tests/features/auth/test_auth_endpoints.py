"""Authentication endpoint tests."""

from __future__ import annotations

from tests.factories import DEFAULT_PASSWORD, create_user
from tests.helpers import assert_error, assert_requires_auth


async def test_register_login_refresh_and_me(client_factory) -> None:
    """Auth endpoints support the full token lifecycle."""
    async with client_factory(None) as client:
        registered = await client.post(
            "/v1/auth/register",
            json={
                "email": "new@example.com",
                "phone": "0912345678",
                "password": DEFAULT_PASSWORD,
                "full_name": "New User",
                "role": "CUSTOMER",
            },
        )
        assert registered.status_code == 200
        profile = registered.json()
        assert profile["email"] == "new@example.com"
        assert profile["phone"] == "+84912345678"
        assert profile["role"] == "CUSTOMER"

        duplicate = await client.post(
            "/v1/auth/register",
            json={
                "email": "new@example.com",
                "phone": "0912345679",
                "password": DEFAULT_PASSWORD,
                "full_name": "Duplicate User",
            },
        )
        assert_error(duplicate, 400, "Email already registered")

        login = await client.post(
            "/v1/auth/login",
            json={"email": "new@example.com", "password": DEFAULT_PASSWORD},
        )
        assert login.status_code == 200
        tokens = login.json()
        assert tokens["token_type"] == "bearer"
        assert tokens["expires_in"] == 1800
        assert tokens["access_token"] and tokens["refresh_token"]

        refreshed = await client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert refreshed.status_code == 200
        assert refreshed.json()["access_token"]

        me = await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["id"] == profile["id"]


async def test_login_invalid_credentials(client_factory) -> None:
    """Invalid login details return a generic 401."""
    async with client_factory(None) as client:
        response = await client.post(
            "/v1/auth/login",
            json={"email": "missing@example.com", "password": DEFAULT_PASSWORD},
        )
        assert_error(response, 401, "Invalid credentials")


async def test_refresh_invalid_token(client_factory) -> None:
    """Invalid refresh tokens return 401."""
    async with client_factory(None) as client:
        response = await client.post("/v1/auth/refresh", json={"refresh_token": "bad"})
        assert_error(response, 401, "Invalid refresh token")


async def test_me_requires_auth(client_factory) -> None:
    """Current-user profile requires authentication."""
    async with client_factory(None) as client:
        await assert_requires_auth(client, "GET", "/v1/auth/me")


async def test_me_uses_authenticated_user(client_factory, session) -> None:
    """Current-user profile reflects the authenticated user."""
    user = await create_user(session, full_name="Authenticated User")
    async with client_factory(user) as client:
        response = await client.get("/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["id"] == str(user.id)
    assert response.json()["full_name"] == "Authenticated User"
