"""Restaurant API schemas."""

from __future__ import annotations

from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import RestaurantStatus


class RestaurantBase(BaseModel):
    """Base restaurant schema."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    street: str = Field(..., min_length=1, max_length=255)
    ward: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    phone: str = Field(..., min_length=10, max_length=15)
    email: str | None = Field(default=None, max_length=255)
    cuisine_type: str | None = Field(default=None, max_length=100)
    opening_time: time
    closing_time: time
    delivery_radius_km: Decimal = Field(..., ge=Decimal("0.1"), le=Decimal("100.0"))
    minimum_order_amount: Decimal = Field(..., ge=Decimal("0"))
    delivery_fee: Decimal = Field(..., ge=Decimal("0"))
    status: RestaurantStatus = RestaurantStatus.PENDING
    avatar_url: str | None = None
    cover_url: str | None = None


class RestaurantCreate(RestaurantBase):
    """Restaurant creation schema."""

    model_config = ConfigDict(extra="forbid")


class RestaurantUpdate(BaseModel):
    """Restaurant update schema."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    street: str | None = Field(default=None, min_length=1, max_length=255)
    ward: str | None = Field(default=None, min_length=1, max_length=100)
    district: str | None = Field(default=None, min_length=1, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    phone: str | None = Field(default=None, min_length=10, max_length=15)
    email: str | None = Field(default=None, max_length=255)
    cuisine_type: str | None = Field(default=None, max_length=100)
    opening_time: time | None = None
    closing_time: time | None = None
    delivery_radius_km: Decimal | None = Field(default=None, ge=Decimal("0.1"), le=Decimal("100.0"))
    minimum_order_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    delivery_fee: Decimal | None = Field(default=None, ge=Decimal("0"))
    status: RestaurantStatus | None = None
    avatar_url: str | None = None
    cover_url: str | None = None


class RestaurantResponse(RestaurantBase):
    """Restaurant response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    owner_id: UUID
    created_at: datetime
    updated_at: datetime


class RestaurantSummaryResponse(BaseModel):
    """Restaurant summary response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    name: str
    cuisine_type: str | None = None
    status: RestaurantStatus
    minimum_order_amount: Decimal
    delivery_fee: Decimal
    avatar_url: str | None = None
    cover_url: str | None = None
