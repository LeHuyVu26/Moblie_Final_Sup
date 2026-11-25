"""Authentication and authorization dependencies."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_session
from app.core.security import ACCESS_TOKEN_TYPE, TokenError, decode_token, token_subject
from app.domain.entities import User
from app.domain.enums import UserRole
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_session)]


async def _resolve_user(
    credentials: HTTPAuthorizationCredentials | None,
    session: AsyncSession,
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = decode_token(credentials.credentials, expected_type=ACCESS_TOKEN_TYPE)
        user_id = token_subject(payload)
    except TokenError:
        return None

    repository = UserRepository(session)
    user = await repository.get(user_id)
    if user is None or not user.is_active:
        return None
    return user


async def get_optional_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User | None:
    """Return the authenticated user, or None when unauthenticated."""
    return await _resolve_user(credentials, session)


async def get_current_user(
    user: Annotated[User | None, Depends(get_optional_user)],
) -> User:
    """Require an authenticated user."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def require_roles(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """Build a dependency that requires one of the given roles."""
    allowed = frozenset(roles)

    async def _dependency(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _dependency
