"""Security helper tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from jose import jwt

from app.config.settings import get_settings
from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    token_subject,
    verify_password,
)


def test_password_hashing() -> None:
    """Hashes are salted and verify only the original password."""
    password_hash = hash_password("Password123")

    assert password_hash != "Password123"
    assert verify_password("Password123", password_hash) is True
    assert verify_password("WrongPassword", password_hash) is False


def test_create_and_decode_access_token() -> None:
    """Access tokens carry subject, type, timestamps, and optional role."""
    subject = uuid.uuid4()

    token = create_access_token(subject, role="STAFF")
    payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)

    assert token_subject(payload) == subject
    assert payload["type"] == ACCESS_TOKEN_TYPE
    assert payload["role"] == "STAFF"
    assert payload["iat"] <= payload["exp"]


def test_create_and_decode_refresh_token() -> None:
    """Refresh tokens use the refresh token type."""
    subject = uuid.uuid4()

    token = create_refresh_token(subject)
    payload = decode_token(token, expected_type=REFRESH_TOKEN_TYPE)

    assert token_subject(payload) == subject
    assert payload["type"] == REFRESH_TOKEN_TYPE
    assert "role" not in payload


def test_decode_token_rejects_wrong_type() -> None:
    """A refresh token cannot satisfy an access-token check."""
    token = create_refresh_token(uuid.uuid4())

    with pytest.raises(TokenError, match="Expected access token"):
        decode_token(token, expected_type=ACCESS_TOKEN_TYPE)


def test_decode_token_rejects_invalid_token() -> None:
    """Malformed and expired tokens raise TokenError."""
    with pytest.raises(TokenError, match="Invalid or expired token"):
        decode_token("not-a-token")

    expired = create_access_token(uuid.uuid4(), expires_delta=timedelta(seconds=-1))
    with pytest.raises(TokenError, match="Invalid or expired token"):
        decode_token(expired)


def test_decode_token_rejects_missing_or_invalid_subject() -> None:
    """Decoded tokens must contain a UUID subject."""
    settings = get_settings()
    now = datetime.now(UTC)
    base_payload: dict[str, Any] = {
        "type": ACCESS_TOKEN_TYPE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
    }

    missing_sub = jwt.encode(base_payload, settings.secret_key, algorithm=settings.algorithm)
    with pytest.raises(TokenError, match="Token missing subject"):
        decode_token(missing_sub)

    invalid_sub = jwt.encode(
        {**base_payload, "sub": "not-a-uuid"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    with pytest.raises(TokenError, match="Token subject is not a valid UUID"):
        token_subject(decode_token(invalid_sub))
