"""Authentication and pagination dependency tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.deps.auth import get_current_user, get_optional_user, require_roles
from app.api.deps.pagination import Pagination, pagination_params
from app.config.settings import get_settings
from app.core.security import create_access_token
from app.domain.enums import UserRole
from tests.factories import create_user


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def test_get_optional_user_without_credentials(session) -> None:
    """Missing credentials resolve to no user."""
    assert await get_optional_user(session, None) is None


async def test_get_optional_user_with_valid_token(session) -> None:
    """A valid access token resolves to the matching active user."""
    user = await create_user(session, role=UserRole.CUSTOMER)
    token = create_access_token(user.id)

    resolved = await get_optional_user(session, _credentials(token))

    assert resolved is not None
    assert resolved.id == user.id
    assert resolved.email == user.email


async def test_get_optional_user_rejects_invalid_or_inactive(session) -> None:
    """Invalid tokens and inactive users resolve to no user."""
    user = await create_user(session, is_active=False)
    token = create_access_token(user.id)

    assert await get_optional_user(session, _credentials("invalid")) is None
    assert await get_optional_user(session, _credentials(token)) is None
    assert await get_optional_user(session, _credentials(create_access_token(uuid.uuid4()))) is None


async def test_get_current_user_requires_user() -> None:
    """get_current_user raises a bearer-auth error when no user is resolved."""
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)

    error = exc_info.value
    assert error.status_code == 401
    assert error.detail == "Not authenticated"
    assert error.headers == {"WWW-Authenticate": "Bearer"}


async def test_get_current_user_returns_resolved_user(session) -> None:
    """get_current_user returns an authenticated user unchanged."""
    user = await create_user(session)

    assert await get_current_user(user) is user


async def test_require_roles_allows_allowed_role(session) -> None:
    """The role dependency returns users with an allowed role."""
    staff = await create_user(session, role=UserRole.STAFF)
    dependency = require_roles(UserRole.STAFF, UserRole.OWNER)

    assert await dependency(staff) is staff


async def test_require_roles_rejects_disallowed_role(session) -> None:
    """The role dependency raises 403 for other roles."""
    customer = await create_user(session, role=UserRole.CUSTOMER)
    dependency = require_roles(UserRole.STAFF)

    with pytest.raises(HTTPException) as exc_info:
        await dependency(customer)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions"


def test_pagination_defaults_and_page_calculation() -> None:
    """Pagination defaults to page one and derives page from offset."""
    pagination = pagination_params()

    assert pagination == Pagination(limit=20, offset=0)
    assert pagination.page == 1


def test_pagination_clamps_size_and_calculates_offset() -> None:
    """Page size is clamped to the configured maximum."""
    max_size = get_settings().max_page_size

    pagination = pagination_params(page=3, size=max_size + 50)

    assert pagination.limit == max_size
    assert pagination.offset == 2 * max_size
    assert pagination.page == 3
