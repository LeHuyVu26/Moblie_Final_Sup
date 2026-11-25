"""Domain entities."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Any

from pydantic import Field, StringConstraints

from app.domain.base import DomainEntity
from app.domain.enums import (
    DeliveryProvider,
    DeliveryStatus,
    MenuItemStatus,
    OrderStatus,
    PaymentStatus,
    PromotionType,
    UserRole,
)
from app.domain.value_objects import Address, Coordinates, Money, PhoneNumber


class User(DomainEntity):
    """User entity."""

    email: Annotated[str, StringConstraints(pattern=r"^[^@]+@[^@]+\.[^@]+$")]
    phone: PhoneNumber
    full_name: str = Field(..., min_length=1, max_length=100)
    password_hash: str
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    avatar_url: str | None = None
    last_login_at: datetime | None = None


class Restaurant(DomainEntity):
    """Restaurant entity."""

    owner_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    address: Address
    phone: PhoneNumber
    email: Annotated[str, StringConstraints(pattern=r"^[^@]+@[^@]+\.[^@]+$")]
    logo_url: str | None = None
    cover_image_url: str | None = None
    is_active: bool = True
    opening_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    closing_time: str = Field(..., pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    min_order_amount: Money = Field(default_factory=lambda: Money(amount=Decimal("0")))
    delivery_fee: Money = Field(default_factory=lambda: Money(amount=Decimal("0")))
    delivery_radius_km: Decimal = Field(default=Decimal("5.0"), ge=0, le=50)
    rating: Decimal = Field(default=Decimal("0.0"), ge=0, le=5, decimal_places=1)
    total_reviews: int = Field(default=0, ge=0)


class Category(DomainEntity):
    """Menu category entity."""

    restaurant_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    image_url: str | None = None
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True


class MenuItem(DomainEntity):
    """Menu item entity."""

    restaurant_id: uuid.UUID
    category_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    price: Money
    original_price: Money | None = None
    image_url: str | None = None
    status: MenuItemStatus = MenuItemStatus.AVAILABLE
    is_vegetarian: bool = False
    is_vegan: bool = False
    is_spicy: bool = False
    preparation_time_minutes: int = Field(default=15, ge=1, le=120)
    calories: int | None = Field(default=None, ge=0)
    allergens: list[str] = Field(default_factory=list)
    display_order: int = Field(default=0, ge=0)


class Promotion(DomainEntity):
    """Promotion entity."""

    restaurant_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    type: PromotionType
    value: Decimal = Field(..., ge=0, decimal_places=2)
    min_order_amount: Money | None = None
    max_discount_amount: Money | None = None
    usage_limit: int | None = Field(default=None, ge=1)
    usage_count: int = Field(default=0, ge=0)
    user_usage_limit: int = Field(default=1, ge=1)
    start_at: datetime
    end_at: datetime
    is_active: bool = True
    applicable_menu_item_ids: list[uuid.UUID] = Field(default_factory=list)
    applicable_category_ids: list[uuid.UUID] = Field(default_factory=list)

    def is_valid(self, at: datetime | None = None) -> bool:
        """Check if promotion is currently valid."""
        now = at or datetime.utcnow()
        return (
            self.is_active
            and self.start_at <= now <= self.end_at
            and (self.usage_limit is None or self.usage_count < self.usage_limit)
        )


class OrderItem(DomainEntity):
    """Order item entity."""

    order_id: uuid.UUID
    menu_item_id: uuid.UUID
    menu_item_name: str
    menu_item_price: Money
    quantity: int = Field(..., ge=1)
    note: str | None = None
    subtotal: Money

    @classmethod
    def create(
        cls,
        *,
        order_id: uuid.UUID,
        menu_item_id: uuid.UUID,
        menu_item_name: str,
        menu_item_price: Money,
        quantity: int,
        note: str | None = None,
    ) -> OrderItem:
        """Create order item with calculated subtotal."""
        return cls(
            order_id=order_id,
            menu_item_id=menu_item_id,
            menu_item_name=menu_item_name,
            menu_item_price=menu_item_price,
            quantity=quantity,
            note=note,
            subtotal=Money(amount=menu_item_price.amount * quantity),
        )


class Order(DomainEntity):
    """Order entity."""

    customer_id: uuid.UUID
    restaurant_id: uuid.UUID
    status: OrderStatus = OrderStatus.PENDING
    items: list[OrderItem] = Field(default_factory=list)
    subtotal: Money = Field(default_factory=lambda: Money(amount=Decimal("0")))
    delivery_fee: Money = Field(default_factory=lambda: Money(amount=Decimal("0")))
    discount_amount: Money = Field(default_factory=lambda: Money(amount=Decimal("0")))
    total_amount: Money = Field(default_factory=lambda: Money(amount=Decimal("0")))
    promotion_id: uuid.UUID | None = None
    promotion_code: str | None = None
    delivery_address: Address
    delivery_coordinates: Coordinates | None = None
    customer_note: str | None = None
    restaurant_note: str | None = None
    estimated_preparation_time_minutes: int = Field(default=30, ge=1)
    confirmed_at: datetime | None = None
    ready_at: datetime | None = None
    dispatched_at: datetime | None = None
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None

    def calculate_totals(self) -> None:
        """Recalculate order totals."""
        subtotal_amount = sum(item.subtotal.amount for item in self.items)
        self.subtotal = Money(amount=Decimal(str(subtotal_amount)))
        self.total_amount = self.subtotal + self.delivery_fee - self.discount_amount
        self.touch()

    def can_transition_to(self, new_status: OrderStatus) -> bool:
        """Check if order can transition to new status."""
        valid_transitions: dict[OrderStatus, list[OrderStatus]] = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.READY_FOR_PICKUP, OrderStatus.CANCELLED],
            OrderStatus.READY_FOR_PICKUP: [OrderStatus.DISPATCHED, OrderStatus.CANCELLED],
            OrderStatus.DISPATCHED: [OrderStatus.DELIVERING, OrderStatus.CANCELLED],
            OrderStatus.DELIVERING: [OrderStatus.DELIVERED],
            OrderStatus.DELIVERED: [OrderStatus.REFUNDED],
            OrderStatus.CANCELLED: [],
            OrderStatus.REFUNDED: [],
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status: OrderStatus) -> None:
        """Transition order to new status with timestamp."""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")

        now = datetime.utcnow()
        self.status = new_status

        if new_status == OrderStatus.CONFIRMED:
            self.confirmed_at = now
        elif new_status == OrderStatus.READY_FOR_PICKUP:
            self.ready_at = now
        elif new_status == OrderStatus.DISPATCHED:
            self.dispatched_at = now
        elif new_status == OrderStatus.DELIVERED:
            self.delivered_at = now
        elif new_status == OrderStatus.CANCELLED:
            self.cancelled_at = now

        self.touch()


class Payment(DomainEntity):
    """Payment entity."""

    order_id: uuid.UUID
    amount: Money
    status: PaymentStatus = PaymentStatus.PENDING
    provider: str = "MOCK"
    provider_transaction_id: str | None = None
    provider_response: dict[str, Any] = Field(default_factory=dict)
    paid_at: datetime | None = None
    failed_at: datetime | None = None
    failure_reason: str | None = None


class Delivery(DomainEntity):
    """Delivery entity."""

    order_id: uuid.UUID
    provider: DeliveryProvider
    provider_order_id: str | None = None
    status: DeliveryStatus = DeliveryStatus.PENDING_DISPATCH
    driver_name: str | None = None
    driver_phone: PhoneNumber | None = None
    driver_vehicle: str | None = None
    driver_license_plate: str | None = None
    driver_current_location: Coordinates | None = None
    pickup_address: Address
    pickup_coordinates: Coordinates | None = None
    dropoff_address: Address
    dropoff_coordinates: Coordinates | None = None
    distance_km: Decimal | None = Field(default=None, ge=0)
    estimated_duration_minutes: int | None = Field(default=None, ge=1)
    fee: Money = Field(default_factory=lambda: Money(amount=Decimal("0")))
    assigned_at: datetime | None = None
    picked_up_at: datetime | None = None
    delivered_at: datetime | None = None
    failed_at: datetime | None = None
    failure_reason: str | None = None
    tracking_url: str | None = None

    def can_transition_to(self, new_status: DeliveryStatus) -> bool:
        """Check if delivery can transition to new status."""
        valid_transitions = {
            DeliveryStatus.PENDING_DISPATCH: [DeliveryStatus.DRIVER_ASSIGNED, DeliveryStatus.CANCELLED],
            DeliveryStatus.DRIVER_ASSIGNED: [DeliveryStatus.DRIVER_EN_ROUTE_TO_PICKUP, DeliveryStatus.CANCELLED],
            DeliveryStatus.DRIVER_EN_ROUTE_TO_PICKUP: [DeliveryStatus.PICKED_UP, DeliveryStatus.CANCELLED],
            DeliveryStatus.PICKED_UP: [DeliveryStatus.IN_TRANSIT, DeliveryStatus.CANCELLED],
            DeliveryStatus.IN_TRANSIT: [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED],
            DeliveryStatus.DELIVERED: [],
            DeliveryStatus.FAILED: [DeliveryStatus.CANCELLED],
            DeliveryStatus.CANCELLED: [],
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status: DeliveryStatus) -> None:
        """Transition delivery to new status with timestamp."""
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")

        now = datetime.utcnow()
        self.status = new_status

        if new_status == DeliveryStatus.DRIVER_ASSIGNED:
            self.assigned_at = now
        elif new_status == DeliveryStatus.PICKED_UP:
            self.picked_up_at = now
        elif new_status == DeliveryStatus.DELIVERED:
            self.delivered_at = now
        elif new_status == DeliveryStatus.FAILED:
            self.failed_at = now

        self.touch()


class Review(DomainEntity):
    """Review entity."""

    customer_id: uuid.UUID
    restaurant_id: uuid.UUID
    order_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None
    images: list[str] = Field(default_factory=list)
    is_verified: bool = True
