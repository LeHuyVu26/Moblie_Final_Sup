"""Authentication controller."""

from collections.abc import Callable
from typing import Any, TypeVar, cast

from fastapi import HTTPException, status
from fastapi_controller import controller

from app.api.controllers.base import BaseController
from app.api.deps.auth import CurrentUser, DbSession
from app.api.mappers import map_user_profile
from app.api.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.api.schemas.users import UserProfileResponse
from app.services.auth import AuthService

F = TypeVar("F", bound=Callable[..., Any])


def typed_post(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.post."""
    return cast(Callable[[F], F], controller.post(path))


def typed_get(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.get."""
    return cast(Callable[[F], F], controller.get(path))


class AuthController(BaseController):  # type: ignore[misc]
    """Authentication endpoints."""

    @typed_post("/register")
    async def register(self, request: RegisterRequest, session: DbSession) -> UserProfileResponse:
        """Register a new user."""
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

        return map_user_profile(user)

    @typed_post("/login")
    async def login(self, request: LoginRequest, session: DbSession) -> TokenResponse:
        """Login and get tokens."""
        service = AuthService(session)
        try:
            access_token, refresh_token, _ = await service.login(email=str(request.email), password=request.password)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,
        )

    @typed_post("/refresh")
    async def refresh(self, request: RefreshTokenRequest, session: DbSession) -> TokenResponse:
        """Refresh access token."""
        service = AuthService(session)
        try:
            access_token, refresh_token = await service.refresh_tokens(refresh_token=request.refresh_token)
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,
        )

    @typed_get("/me")
    async def me(self, current_user: CurrentUser) -> UserProfileResponse:
        """Get current user profile."""
        return map_user_profile(current_user)
