"""Security utilities: password hashing and JWT tokens."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.settings import get_settings

PASSWORD_CONTEXT: Final[CryptContext] = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_TYPE: Final[str] = "access"
REFRESH_TOKEN_TYPE: Final[str] = "refresh"


class TokenError(Exception):
    """Raised when a JWT token is invalid or expired."""


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return PASSWORD_CONTEXT.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a hash."""
    return PASSWORD_CONTEXT.verify(plain_password, password_hash)


def _create_token(
    *,
    subject: uuid.UUID,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(
    subject: uuid.UUID,
    *,
    role: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    delta = expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    extra = {"role": role} if role else None
    return _create_token(
        subject=subject,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=delta,
        extra_claims=extra,
    )


def create_refresh_token(
    subject: uuid.UUID,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT refresh token."""
    settings = get_settings()
    delta = expires_delta or timedelta(days=settings.refresh_token_expire_days)
    return _create_token(
        subject=subject,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=delta,
    )


def decode_token(token: str, *, expected_type: str | None = None) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    settings = get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise TokenError(f"Expected {expected_type} token")

    if "sub" not in payload:
        raise TokenError("Token missing subject")

    return payload


def token_subject(payload: dict[str, Any]) -> uuid.UUID:
    """Extract the subject UUID from a decoded token payload."""
    try:
        return uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise TokenError("Token subject is not a valid UUID") from exc
