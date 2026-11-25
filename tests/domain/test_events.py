"""Domain event tests."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.domain.base import DomainEvent
from app.domain.enums import DeliveryStatus, OrderStatus
from app.domain.events import (
    DeliveryStatusChanged,
    OrderCreated,
    OrderStatusChanged,
    PaymentCompleted,
    ReviewCreated,
    UserRegistered,
)
from app.domain.value_objects import Coordinates, Money


def test_domain_event_defaults() -> None:
    """Domain events get identity, timestamp, and class-name event type."""

    class CustomEvent(DomainEvent):
        event_type: str = ""
        value: int

    event = CustomEvent(value=1)

    assert isinstance(event.event_id, uuid.UUID)
    assert event.event_type == "CustomEvent"
    assert event.occurred_at <= event.occurred_at


def test_order_events() -> None:
    """Order events carry their domain payloads."""
    order_id = uuid.uuid4()
    customer_id = uuid.uuid4()
    restaurant_id = uuid.uuid4()

    created = OrderCreated(
        order_id=order_id,
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        total_amount=Money(amount=Decimal("130000")),
        items_count=2,
    )
    changed = OrderStatusChanged(
        order_id=order_id,
        old_status=OrderStatus.PENDING,
        new_status=OrderStatus.CONFIRMED,
        changed_by=customer_id,
    )

    assert created.event_type == "OrderCreated"
    assert created.total_amount.amount == Decimal("130000.00")
    assert changed.old_status == OrderStatus.PENDING.value
    assert changed.new_status == OrderStatus.CONFIRMED.value


def test_payment_delivery_and_review_events() -> None:
    """Other event types preserve provider and status details."""
    payment = PaymentCompleted(
        payment_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        amount=Money(amount=Decimal("50000")),
        provider="MOMO",
        provider_transaction_id="MOCK-TXN",
    )
    delivery = DeliveryStatusChanged(
        delivery_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        old_status=DeliveryStatus.PICKED_UP,
        new_status=DeliveryStatus.IN_TRANSIT,
        driver_location=Coordinates(latitude=10.0, longitude=106.0),
    )
    review = ReviewCreated(
        review_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        restaurant_id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        rating=5,
    )
    registered = UserRegistered(
        user_id=uuid.uuid4(),
        email="user@example.com",
        role="CUSTOMER",
    )

    assert payment.provider_transaction_id == "MOCK-TXN"
    assert delivery.driver_location is not None
    assert delivery.driver_location.latitude == 10.0
    assert review.rating == 5
    assert registered.role == "CUSTOMER"
