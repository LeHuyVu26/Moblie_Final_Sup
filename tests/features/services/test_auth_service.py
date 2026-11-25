"""Tests for AuthService."""

from __future__ import annotations

import uuid

import pytest

from app.core.security import TokenError
from app.domain.enums import UserRole
from app.domain.value_objects import PhoneNumber
from app.services.auth import AuthService
from tests.factories import create_user


async def test_register_creates_user(session) -> None:
    """Register creates a new user with hashed password."""
    service = AuthService(session)
    user = await service.register(
        email="new@example.com",
        phone="0912345678",
        password="Password123",
        full_name="New User",
        role=UserRole.CUSTOMER,
    )

    assert user.email == "new@example.com"
    assert user.phone.number == "+84912345678"
    assert user.full_name == "New User"
    assert user.role == UserRole.CUSTOMER
    assert user.is_active is True
    assert user.password_hash != "Password123"


async def test_register_duplicate_email_raises(session) -> None:
    """Registering with an existing email raises ValueError."""
    await create_user(session, email="dup@example.com")
    service = AuthService(session)

    with pytest.raises(ValueError, match="Email already registered"):
        await service.register(
            email="dup@example.com",
            phone="0912345679",
            password="Password123",
            full_name="Duplicate",
        )


async def test_register_duplicate_phone_raises(session) -> None:
    """Registering with an existing normalized phone raises ValueError."""
    await create_user(session, phone="0912345678")
    service = AuthService(session)

    with pytest.raises(ValueError, match="Phone number already registered"):
        await service.register(
            email="new@example.com",
            phone=PhoneNumber.normalize("0912345678"),
            password="Password123",
            full_name="Duplicate",
        )


async def test_register_duplicate_phone_in_raw_format_is_not_detected(session) -> None:
    """Document current behavior: duplicate check compares raw input to stored +84 phone."""
    await create_user(session, phone="0912345678")
    service = AuthService(session)

    user = await service.register(
        email="raw-phone@example.com",
        phone="0912345678",
        password="Password123",
        full_name="Raw Phone",
    )

    assert user.phone.number == "+84912345678"


async def test_login_success(session) -> None:
    """Login returns access and refresh tokens for valid credentials."""
    await create_user(session, email="login@example.com", password="Password123")
    service = AuthService(session)

    access, refresh, user = await service.login(email="login@example.com", password="Password123")

    assert isinstance(access, str) and len(access) > 0
    assert isinstance(refresh, str) and len(refresh) > 0
    assert user.email == "login@example.com"
    assert user.last_login_at is not None


async def test_login_invalid_email_raises(session) -> None:
    """Login with unknown email raises ValueError."""
    service = AuthService(session)

    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login(email="unknown@example.com", password="Password123")


async def test_login_inactive_user_raises(session) -> None:
    """Login with inactive user raises ValueError."""
    await create_user(session, email="inactive@example.com", is_active=False)
    service = AuthService(session)

    with pytest.raises(ValueError, match="Account is deactivated"):
        await service.login(email="inactive@example.com", password="Password123")


async def test_login_wrong_password_raises(session) -> None:
    """Login with wrong password raises ValueError."""
    await create_user(session, email="wrongpass@example.com", password="Password123")
    service = AuthService(session)

    with pytest.raises(ValueError, match="Invalid credentials"):
        await service.login(email="wrongpass@example.com", password="WrongPassword")


async def test_refresh_tokens_success(session) -> None:
    """Refresh tokens returns new access and refresh tokens."""
    await create_user(session, email="refresh@example.com")
    service = AuthService(session)

    _, refresh, _ = await service.login(email="refresh@example.com", password="Password123")
    new_access, new_refresh = await service.refresh_tokens(refresh_token=refresh)

    assert isinstance(new_access, str) and len(new_access) > 0
    assert isinstance(new_refresh, str) and len(new_refresh) > 0
    assert new_access != new_refresh


async def test_refresh_tokens_invalid_token_raises(session) -> None:
    """Refresh with invalid token raises TokenError."""
    service = AuthService(session)

    with pytest.raises(TokenError, match="Invalid or expired token"):
        await service.refresh_tokens(refresh_token="invalid.token.here")


async def test_refresh_tokens_wrong_type_raises(session) -> None:
    """Refresh with access token instead of refresh token raises TokenError."""
    await create_user(session, email="type@example.com")
    service = AuthService(session)

    access, _, _ = await service.login(email="type@example.com", password="Password123")

    with pytest.raises(TokenError, match="Expected refresh token"):
        await service.refresh_tokens(refresh_token=access)


async def test_refresh_tokens_deleted_user_raises(session) -> None:
    """Refresh for deleted user raises ValueError."""
    user = await create_user(session, email="deleted@example.com")
    service = AuthService(session)

    _, refresh, _ = await service.login(email="deleted@example.com", password="Password123")

    # Delete the user
    from app.repositories.user import UserRepository

    await UserRepository(session).remove(user.id)

    with pytest.raises(ValueError, match="User not found or inactive"):
        await service.refresh_tokens(refresh_token=refresh)


async def test_change_password_success(session) -> None:
    """Change password updates the password hash."""
    user = await create_user(session, email="changepass@example.com", password="OldPass123")
    service = AuthService(session)

    await service.change_password(user_id=user.id, current_password="OldPass123", new_password="NewPass123")

    # Verify new password works
    access, _, _ = await service.login(email="changepass@example.com", password="NewPass123")
    assert isinstance(access, str)


async def test_change_password_wrong_current_raises(session) -> None:
    """Change password with wrong current password raises ValueError."""
    user = await create_user(session, email="wrongcurrent@example.com", password="OldPass123")
    service = AuthService(session)

    with pytest.raises(ValueError, match="Current password is incorrect"):
        await service.change_password(user_id=user.id, current_password="WrongPass", new_password="NewPass123")


async def test_change_password_user_not_found_raises(session) -> None:
    """Change password for non-existent user raises ValueError."""
    service = AuthService(session)

    with pytest.raises(ValueError, match="User not found"):
        await service.change_password(user_id=uuid.uuid4(), current_password="OldPass123", new_password="NewPass123")


async def test_get_user_from_token_success(session) -> None:
    """Get user from valid access token returns user."""
    user = await create_user(session, email="token@example.com")
    service = AuthService(session)

    access, _, _ = await service.login(email="token@example.com", password="Password123")
    fetched = await service.get_user_from_token(token=access)

    assert fetched is not None
    assert fetched.id == user.id


async def test_get_user_from_token_invalid_returns_none(session) -> None:
    """Get user from invalid token returns None."""
    service = AuthService(session)

    result = await service.get_user_from_token(token="invalid.token.here")
    assert result is None


async def test_get_user_by_id(session) -> None:
    """Get user by ID returns user."""
    user = await create_user(session, email="byid@example.com")
    service = AuthService(session)

    fetched = await service.get_user_by_id(user.id)
    assert fetched is not None
    assert fetched.id == user.id


async def test_get_user_by_id_not_found(session) -> None:
    """Get user by unknown ID returns None."""
    service = AuthService(session)

    result = await service.get_user_by_id(uuid.uuid4())
    assert result is None
