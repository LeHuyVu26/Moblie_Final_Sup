"""User API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import UserRole


class UserBase(BaseModel):
    """Base user schema."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole
    is_active: bool = True


class UserCreate(UserBase):
    """User creation schema (admin only)."""

    model_config = ConfigDict(extra="forbid")

    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseModel):
    """User update schema."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=10, max_length=15)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """User response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class UserProfileResponse(BaseModel):
    """Current user profile response."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    email: EmailStr
    phone: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
