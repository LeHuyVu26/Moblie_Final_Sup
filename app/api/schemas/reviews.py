"""Review API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewBase(BaseModel):
    """Base review schema."""

    model_config = ConfigDict(extra="forbid")

    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    images: list[str] = Field(default_factory=list)


class ReviewCreate(ReviewBase):
    """Review creation schema."""

    model_config = ConfigDict(extra="forbid")


class ReviewUpdate(BaseModel):
    """Review update schema."""

    model_config = ConfigDict(extra="forbid")

    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    images: list[str] | None = None


class ReviewResponse(ReviewBase):
    """Review response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    order_id: UUID
    restaurant_id: UUID
    customer_id: UUID
    customer_name: str
    created_at: datetime
    updated_at: datetime
