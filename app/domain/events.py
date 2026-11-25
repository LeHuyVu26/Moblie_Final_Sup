"""Domain events."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.domain.base import DomainEvent
from app.domain.enums import DeliveryStatus, OrderStatus
from app.domain.value_objects import Coordinates, Money


class OrderCreated(DomainEvent):
    """Event fired when an order is created."""

    event_type: str = "OrderCreated"
    order_id: uuid.UUID
    customer_id: uuid.UUID
    restaurant_id: uuid.UUID
    total_amount: Money
    items_count: int


class OrderStatusChanged(DomainEvent):
    """Event fired when order status changes."""

    event_type: str = "OrderStatusChanged"
    order_id: uuid.UUID
    old_status: OrderStatus
    new_status: OrderStatus
    changed_by: uuid.UUID | None = None
    reason: str | None = None


class OrderCancelled(DomainEvent):
    """Event fired when an order is cancelled."""

    event_type: str = "OrderCancelled"
    order_id: uuid.UUID
    customer_id: uuid.UUID
    restaurant_id: uuid.UUID
    reason: str
    cancelled_by: uuid.UUID


class PaymentCompleted(DomainEvent):
    """Event fired when payment is completed."""

    event_type: str = "PaymentCompleted"
    payment_id: uuid.UUID
    order_id: uuid.UUID
    amount: Money
    provider: str
    provider_transaction_id: str | None = None


class PaymentFailed(DomainEvent):
    """Event fired when payment fails."""

    event_type: str = "PaymentFailed"
    payment_id: uuid.UUID
    order_id: uuid.UUID
    amount: Money
    provider: str
    failure_reason: str


class DeliveryDispatched(DomainEvent):
    """Event fired when delivery is dispatched to provider."""

    event_type: str = "DeliveryDispatched"
    delivery_id: uuid.UUID
    order_id: uuid.UUID
    provider: str
    provider_order_id: str | None = None


class DeliveryStatusChanged(DomainEvent):
    """Event fired when delivery status changes."""

    event_type: str = "DeliveryStatusChanged"
    delivery_id: uuid.UUID
    order_id: uuid.UUID
    old_status: DeliveryStatus
    new_status: DeliveryStatus
    driver_location: Coordinates | None = None


class DeliveryCompleted(DomainEvent):
    """Event fired when delivery is completed."""

    event_type: str = "DeliveryCompleted"
    delivery_id: uuid.UUID
    order_id: uuid.UUID
    driver_id: str | None = None


class RestaurantCreated(DomainEvent):
    """Event fired when a restaurant is created."""

    event_type: str = "RestaurantCreated"
    restaurant_id: uuid.UUID
    owner_id: uuid.UUID
    name: str


class MenuItemCreated(DomainEvent):
    """Event fired when a menu item is created."""

    event_type: str = "MenuItemCreated"
    menu_item_id: uuid.UUID
    restaurant_id: uuid.UUID
    category_id: uuid.UUID
    name: str
    price: Money


class PromotionCreated(DomainEvent):
    """Event fired when a promotion is created."""

    event_type: str = "PromotionCreated"
    promotion_id: uuid.UUID
    restaurant_id: uuid.UUID
    name: str
    type: str
    value: Decimal


class UserRegistered(DomainEvent):
    """Event fired when a user registers."""

    event_type: str = "UserRegistered"
    user_id: uuid.UUID
    email: str
    role: str


class ReviewCreated(DomainEvent):
    """Event fired when a review is created."""

    event_type: str = "ReviewCreated"
    review_id: uuid.UUID
    customer_id: uuid.UUID
    restaurant_id: uuid.UUID
    order_id: uuid.UUID
    rating: int
