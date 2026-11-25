"""Application settings tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config.settings import Settings, get_settings


def test_get_settings_is_cached_and_usable() -> None:
    """get_settings returns a stable instance with a valid default secret."""
    first = get_settings()
    second = get_settings()

    assert first is second
    assert len(first.secret_key) >= 32
    assert first.app_name == "Mobile Final - D2C F&B Platform"
    assert first.default_page_size == 20
    assert first.max_page_size == 100


def test_settings_read_environment_case_insensitively(monkeypatch) -> None:
    """Environment variables override defaults regardless of case."""
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("UNKNOWN_SETTING", "ignored")

    settings = Settings(secret_key="x" * 32)

    assert settings.app_name == "Test App"
    assert settings.debug is True
    assert not hasattr(settings, "unknown_setting")


def test_settings_require_long_secret_key() -> None:
    """Short secrets are rejected."""
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(secret_key="short")
