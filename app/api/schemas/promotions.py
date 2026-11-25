"""Promotion API schemas."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import DiscountType, PromotionStatus


class PromotionBase(BaseModel):
    """Base promotion schema."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    discount_type: DiscountType
    discount_value: Decimal = Field(..., ge=Decimal("0"))
    minimum_order_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    maximum_discount_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    start_date: date
    end_date: date
    usage_limit: int | None = Field(default=None, ge=1)
    status: PromotionStatus = PromotionStatus.ACTIVE
    applicable_item_ids: list[UUID] = Field(default_factory=list)
    applicable_category_ids: list[UUID] = Field(default_factory=list)


class PromotionCreate(PromotionBase):
    """Promotion creation schema."""

    model_config = ConfigDict(extra="forbid")


class PromotionUpdate(BaseModel):
    """Promotion update schema."""

    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=Decimal("0"))
    minimum_order_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    maximum_discount_amount: Decimal | None = Field(default=None, ge=Decimal("0"))
    start_date: date | None = None
    end_date: date | None = None
    usage_limit: int | None = Field(default=None, ge=1)
    status: PromotionStatus | None = None
    applicable_item_ids: list[UUID] | None = None
    applicable_category_ids: list[UUID] | None = None


class PromotionResponse(PromotionBase):
    """Promotion response schema."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    restaurant_id: UUID
    created_at: datetime
    updated_at: datetime
