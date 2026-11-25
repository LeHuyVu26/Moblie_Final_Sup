"""Category API schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Base category schema."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    display_order: int = Field(default=0, ge=0)


class CategoryCreate(CategoryBase):
    """Category creation schema."""

    model_config = ConfigDict(extra="forbid")


class CategoryUpdate(BaseModel):
    """Category update schema."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    display_order: int | None = Field(default=None, ge=0)


class CategoryResponse(CategoryBase):
    """Category response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime
