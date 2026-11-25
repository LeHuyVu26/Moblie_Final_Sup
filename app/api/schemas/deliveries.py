"""Delivery API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DeliveryProvider, DeliveryStatus


class DeliveryAddress(BaseModel):
    """Delivery address schema."""

    model_config = ConfigDict(extra="forbid")

    street: str = Field(..., min_length=1, max_length=255)
    ward: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class DeliveryResponse(BaseModel):
    """Delivery response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    order_id: UUID
    status: DeliveryStatus
    provider: DeliveryProvider | None = None
    provider_order_id: str | None = None
    driver_name: str | None = None
    driver_phone: str | None = None
    tracking_url: str | None = None
    pickup_address: DeliveryAddress
    dropoff_address: DeliveryAddress
    fee: Decimal
    estimated_pickup_at: datetime | None = None
    estimated_dropoff_at: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DeliveryDispatchRequest(BaseModel):
    """Manual delivery dispatch request (admin/restaurant)."""

    model_config = ConfigDict(extra="forbid")

    provider: DeliveryProvider


class DeliveryTrackingUpdate(BaseModel):
    """Delivery tracking update from provider webhook."""

    model_config = ConfigDict(extra="forbid")

    status: DeliveryStatus
    driver_name: str | None = None
    driver_phone: str | None = None
    tracking_url: str | None = None
    estimated_pickup_at: datetime | None = None
    estimated_dropoff_at: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
