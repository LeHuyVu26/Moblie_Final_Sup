"""Authentication service."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.entities import User as DomainUser
from app.domain.enums import UserRole
from app.domain.value_objects import PhoneNumber
from app.repositories.user import UserRepository


class AuthService:
    """Authentication service for user registration, login, and token management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)

    async def register(
        self,
        *,
        email: str,
        phone: str,
        password: str,
        full_name: str,
        role: UserRole = UserRole.CUSTOMER,
    ) -> DomainUser:
        """Register a new user."""
        # Check if email already exists
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        # Check if phone already exists
        existing = await self._user_repo.get_by_phone(phone)
        if existing:
            raise ValueError("Phone number already registered")

        # Create user
        user = DomainUser(
            email=email,
            phone=PhoneNumber(number=PhoneNumber.normalize(phone)),
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
        )
        return await self._user_repo.add(user)

    async def login(self, *, email: str, password: str) -> tuple[str, str, DomainUser]:
        """Authenticate user and return access/refresh tokens."""
        user = await self._user_repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        if not verify_password(password, user.password_hash):
            raise ValueError("Invalid credentials")

        # Update last login
        user.last_login_at = datetime.utcnow()
        await self._user_repo.update(user)

        # Generate tokens
        access_token = create_access_token(user.id, role=str(user.role))
        refresh_token = create_refresh_token(user.id)

        return access_token, refresh_token, user

    async def refresh_tokens(self, *, refresh_token: str) -> tuple[str, str]:
        """Refresh access and refresh tokens."""
        payload = decode_token(refresh_token, expected_type=REFRESH_TOKEN_TYPE)
        user_id = uuid.UUID(payload["sub"])

        user = await self._user_repo.get(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        access_token = create_access_token(user.id, role=str(user.role))
        new_refresh_token = create_refresh_token(user.id)

        return access_token, new_refresh_token

    async def change_password(self, *, user_id: uuid.UUID, current_password: str, new_password: str) -> None:
        """Change user password."""
        user = await self._user_repo.get(user_id)
        if not user:
            raise ValueError("User not found")

        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        user.password_hash = hash_password(new_password)
        await self._user_repo.update(user)

    async def get_user_from_token(self, *, token: str) -> DomainUser | None:
        """Get user from access token."""
        try:
            payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
            user_id = uuid.UUID(payload["sub"])
            return await self._user_repo.get(user_id)
        except Exception:
            return None

    async def get_user_by_id(self, user_id: uuid.UUID) -> DomainUser | None:
        """Get user by ID."""
        return await self._user_repo.get(user_id)
