"""Application settings using Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "Mobile Final - D2C F&B Platform"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # Database
    database_url: str = "sqlite+aiosqlite:///./app.db"
    database_echo: bool = False

    # Security
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    # Delivery Providers (Mock)
    ahamove_api_key: str = "mock_ahamove_key"
    ahamove_api_secret: str = "mock_ahamove_secret"
    ahamove_base_url: str = "https://api.ahamove.com/v1"
    lalamove_api_key: str = "mock_lalamove_key"
    lalamove_api_secret: str = "mock_lalamove_secret"
    lalamove_base_url: str = "https://api.lalamove.com/v2"

    # Payment provider settings
    payment_provider: str = "MOCK"
    payment_api_key: str = "mock_payment_key"
    payment_api_secret: str = "mock_payment_secret"
    payment_base_url: str = "https://api.payment.mock/v1"

    # Notification provider settings
    notification_provider: str = "MOCK"
    notification_api_key: str = "mock_notification_key"
    notification_base_url: str = "https://api.notification.mock/v1"

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings(secret_key="your-super-secret-key-change-in-production-min-32-chars")
