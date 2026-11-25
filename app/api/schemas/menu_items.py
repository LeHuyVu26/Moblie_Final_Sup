"""Menu item API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import MenuItemStatus


class MenuItemBase(BaseModel):
    """Base menu item schema."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    price: Decimal = Field(..., gt=Decimal("0"))
    discounted_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    image_url: str | None = None
    status: MenuItemStatus = MenuItemStatus.AVAILABLE
    is_featured: bool = False
    preparation_time_minutes: int = Field(default=15, ge=0)
    allergens: list[str] = Field(default_factory=list)


class MenuItemCreate(MenuItemBase):
    """Menu item creation schema."""

    model_config = ConfigDict(extra="forbid")

    category_id: UUID


class MenuItemUpdate(BaseModel):
    """Menu item update schema."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=Decimal("0"))
    discounted_price: Decimal | None = Field(default=None, ge=Decimal("0"))
    image_url: str | None = None
    category_id: UUID | None = None
    status: MenuItemStatus | None = None
    is_featured: bool | None = None
    preparation_time_minutes: int | None = Field(default=None, ge=0)
    allergens: list[str] | None = None


class MenuItemResponse(MenuItemBase):
    """Menu item response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    restaurant_id: UUID
    category_id: UUID
    created_at: datetime
    updated_at: datetime


class MenuItemSummaryResponse(BaseModel):
    """Menu item summary response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    name: str
    price: Decimal
    discounted_price: Decimal | None = None
    image_url: str | None = None
    status: MenuItemStatus
    preparation_time_minutes: int
