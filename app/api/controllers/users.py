"""User controller."""

from collections.abc import Callable
from typing import Any, TypeVar, cast
from uuid import UUID

from fastapi import HTTPException, status
from fastapi_controller import controller

from app.api.controllers.base import BaseController
from app.api.deps.auth import DbSession, require_roles
from app.api.deps.pagination import PaginationDep
from app.api.mappers import map_page, map_user
from app.api.schemas.auth import ChangePasswordRequest
from app.api.schemas.common import Page
from app.api.schemas.users import UserCreate, UserResponse, UserUpdate
from app.domain.enums import UserRole
from app.services.auth import AuthService

F = TypeVar("F", bound=Callable[..., Any])


def typed_get(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.get."""
    return cast(Callable[[F], F], controller.get(path))


def typed_post(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.post."""
    return cast(Callable[[F], F], controller.post(path))


def typed_patch(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.patch."""
    return cast(Callable[[F], F], controller.patch(path))


class UserController(BaseController):  # type: ignore[misc]
    """User management endpoints."""

    @typed_get("/")
    async def list_users(
        self, session: DbSession, pagination: PaginationDep, current_user: Any = require_roles(UserRole.STAFF)
    ) -> Page[UserResponse]:
        """List users (staff only)."""
        from app.repositories.user import UserRepository

        repo = UserRepository(session)
        users = await repo.list(limit=pagination.limit, offset=pagination.offset)
        return map_page(
            [map_user(u) for u in users],
            total=len(users),
            page=pagination.page,
            size=pagination.limit,
        )

    @typed_get("/{user_id}")
    async def get_user(
        self, user_id: UUID, session: DbSession, current_user: Any = require_roles(UserRole.STAFF)
    ) -> UserResponse:
        """Get user by ID (staff only)."""
        service = AuthService(session)
        user = await service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return map_user(user)

    @typed_post("/")
    async def create_user(
        self, request: UserCreate, session: DbSession, current_user: Any = require_roles(UserRole.STAFF)
    ) -> UserResponse:
        """Create user (staff only)."""
        service = AuthService(session)
        try:
            user = await service.register(
                email=str(request.email),
                phone=request.phone,
                password=request.password,
                full_name=request.full_name,
                role=request.role,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return map_user(user)

    @typed_patch("/{user_id}")
    async def update_user(
        self,
        user_id: UUID,
        request: UserUpdate,
        session: DbSession,
        current_user: Any = require_roles(UserRole.STAFF),
    ) -> UserResponse:
        """Update user (staff only)."""
        from app.repositories.user import UserRepository

        repo = UserRepository(session)
        user = await repo.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        for field, value in request.model_dump(exclude_unset=True).items():
            if hasattr(user, field):
                setattr(user, field, value)
        user.touch()
        saved = await repo.update(user)
        return map_user(saved)

    @typed_post("/{user_id}/change-password")
    async def change_password(
        self,
        user_id: UUID,
        request: ChangePasswordRequest,
        session: DbSession,
        current_user: Any = require_roles(UserRole.STAFF),
    ) -> dict[str, str]:
        """Change user password (staff only)."""
        service = AuthService(session)
        try:
            await service.change_password(
                user_id=user_id,
                current_password=request.current_password,
                new_password=request.new_password,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return {"message": "Password changed"}
