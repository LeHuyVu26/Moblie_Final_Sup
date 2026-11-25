"""Authentication API schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import UserRole


class RegisterRequest(BaseModel):
    """User registration request."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.CUSTOMER


class LoginRequest(BaseModel):
    """User login request."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Token response with access and refresh tokens."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    model_config = ConfigDict(extra="forbid")

    refresh_token: str


class TokenPayload(BaseModel):
    """Decoded token payload."""

    model_config = ConfigDict(extra="forbid")

    sub: str  # user UUID
    type: str  # "access" or "refresh"
    role: str | None = None
    iat: int
    exp: int


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
