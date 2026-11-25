"""Payment API schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.domain.enums import PaymentMethod, PaymentStatus


class PaymentCreate(BaseModel):
    """Payment creation schema."""

    model_config = ConfigDict(extra="forbid")

    order_id: UUID
    method: PaymentMethod


class PaymentMethodSelection(BaseModel):
    """Payment method selection for an existing order."""

    model_config = ConfigDict(extra="forbid")

    method: PaymentMethod


class PaymentResponse(BaseModel):
    """Payment response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    order_id: UUID
    method: PaymentMethod
    amount: Decimal
    status: PaymentStatus
    transaction_id: str | None = None
    paid_at: datetime | None = None
    provider_response: dict[str, object] | None = None
    created_at: datetime
    updated_at: datetime


class PaymentIntentResponse(BaseModel):
    """Payment intent response (for gateway integration)."""

    model_config = ConfigDict(extra="forbid")

    payment_id: UUID
    order_id: UUID
    amount: Decimal
    method: PaymentMethod
    client_secret: str | None = None
    redirect_url: str | None = None
    expires_at: datetime | None = None
