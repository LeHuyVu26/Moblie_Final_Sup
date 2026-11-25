"""Common API schemas shared across all domains."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """Paginated response wrapper."""

    model_config = ConfigDict(extra="forbid")

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(extra="forbid")

    detail: str
    code: str | None = None
    field: str | None = None


class SuccessResponse(BaseModel):
    """Standard success response for simple operations."""

    model_config = ConfigDict(extra="forbid")

    message: str
    data: dict[str, object] | None = None


class MessageResponse(BaseModel):
    """Simple message response."""

    model_config = ConfigDict(extra="forbid")

    message: str
