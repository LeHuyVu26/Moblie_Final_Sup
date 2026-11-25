"""Order API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import OrderStatus, PaymentStatus


class OrderItemCreate(BaseModel):
    """Order item creation schema."""

    model_config = ConfigDict(extra="forbid")

    menu_item_id: UUID
    quantity: int = Field(..., ge=1, le=100)
    special_instructions: str | None = Field(default=None, max_length=500)


class OrderItemResponse(BaseModel):
    """Order item response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    menu_item_id: UUID
    menu_item_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    special_instructions: str | None = None


class OrderAddress(BaseModel):
    """Delivery address schema for orders."""

    model_config = ConfigDict(extra="forbid")

    street: str = Field(..., min_length=1, max_length=255)
    ward: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    contact_name: str | None = Field(default=None, max_length=255)
    contact_phone: str | None = Field(default=None, max_length=15)


class OrderCreate(BaseModel):
    """Order creation schema."""

    model_config = ConfigDict(extra="forbid")

    restaurant_id: UUID
    items: list[OrderItemCreate] = Field(..., min_length=1)
    delivery_address: OrderAddress
    promotion_code: str | None = Field(default=None, max_length=50)
    notes: str | None = Field(default=None, max_length=1000)
    scheduled_for: datetime | None = None


class OrderStatusUpdate(BaseModel):
    """Order status update schema."""

    model_config = ConfigDict(extra="forbid")

    status: OrderStatus
    reason: str | None = Field(default=None, max_length=500)


class OrderResponse(BaseModel):
    """Order response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    customer_id: UUID
    restaurant_id: UUID
    restaurant_name: str
    status: OrderStatus
    payment_status: PaymentStatus
    items: list[OrderItemResponse]
    subtotal: Decimal
    discount_amount: Decimal
    delivery_fee: Decimal
    total_amount: Decimal
    delivery_address: OrderAddress
    promotion_code: str | None = None
    notes: str | None = None
    scheduled_for: datetime | None = None
    created_at: datetime
    updated_at: datetime


class OrderSummaryResponse(BaseModel):
    """Order summary response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    restaurant_name: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: Decimal
    created_at: datetime
