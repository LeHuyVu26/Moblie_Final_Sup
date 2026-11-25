"""Domain entity behavior tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.entities import Delivery, Order, OrderItem, Promotion
from app.domain.enums import DeliveryProvider, DeliveryStatus, OrderStatus, PromotionType
from app.domain.value_objects import Address, Money, PhoneNumber
from tests.factories import address


def _order(status: OrderStatus = OrderStatus.PENDING) -> Order:
    return Order(
        customer_id=uuid.uuid4(),
        restaurant_id=uuid.uuid4(),
        status=status,
        delivery_address=address(),
    )


def _delivery(status: DeliveryStatus = DeliveryStatus.PENDING_DISPATCH) -> Delivery:
    return Delivery(
        order_id=uuid.uuid4(),
        provider=DeliveryProvider.AHAMOVE,
        status=status,
        pickup_address=address(street="Restaurant Street"),
        dropoff_address=address(street="Customer Street"),
    )


def test_order_item_create_calculates_subtotal() -> None:
    """OrderItem.create multiplies unit price by quantity."""
    item = OrderItem.create(
        order_id=uuid.uuid4(),
        menu_item_id=uuid.uuid4(),
        menu_item_name="Pho",
        menu_item_price=Money(amount=Decimal("50000")),
        quantity=2,
        note="No onions",
    )

    assert item.subtotal.amount == Decimal("100000.00")
    assert item.note == "No onions"


def test_order_calculate_totals() -> None:
    """Order totals are recomputed from items, fees, and discounts."""
    order = _order()
    order.items = [
        OrderItem.create(
            order_id=order.id,
            menu_item_id=uuid.uuid4(),
            menu_item_name="Pho",
            menu_item_price=Money(amount=Decimal("50000")),
            quantity=2,
        )
    ]
    order.delivery_fee = Money(amount=Decimal("30000"))
    order.discount_amount = Money(amount=Decimal("20000"))
    original_updated_at = order.updated_at

    order.calculate_totals()

    assert order.subtotal.amount == Decimal("100000.00")
    assert order.total_amount.amount == Decimal("110000.00")
    assert order.updated_at >= original_updated_at


def test_order_transition_sets_timestamps() -> None:
    """Valid order transitions update status and matching timestamps."""
    order = _order()

    order.transition_to(OrderStatus.CONFIRMED)
    assert order.status == OrderStatus.CONFIRMED
    assert order.confirmed_at is not None

    order.transition_to(OrderStatus.PREPARING)
    order.transition_to(OrderStatus.READY_FOR_PICKUP)
    assert order.ready_at is not None

    order.transition_to(OrderStatus.DISPATCHED)
    assert order.dispatched_at is not None

    order.transition_to(OrderStatus.DELIVERING)
    order.transition_to(OrderStatus.DELIVERED)
    assert order.delivered_at is not None

    order.transition_to(OrderStatus.REFUNDED)
    assert order.status == OrderStatus.REFUNDED  # type: ignore[comparison-overlap]


def test_order_rejects_invalid_transition() -> None:
    """Invalid order transitions raise a descriptive error."""
    order = _order(OrderStatus.CONFIRMED)

    assert order.can_transition_to(OrderStatus.DELIVERED) is False
    with pytest.raises(ValueError, match="Cannot transition from CONFIRMED"):
        order.transition_to(OrderStatus.DELIVERED)


def test_delivery_transition_sets_timestamps() -> None:
    """Valid delivery transitions update status and matching timestamps."""
    delivery = _delivery()

    delivery.transition_to(DeliveryStatus.DRIVER_ASSIGNED)
    assert delivery.assigned_at is not None

    delivery.transition_to(DeliveryStatus.DRIVER_EN_ROUTE_TO_PICKUP)
    delivery.transition_to(DeliveryStatus.PICKED_UP)
    assert delivery.picked_up_at is not None

    delivery.transition_to(DeliveryStatus.IN_TRANSIT)
    delivery.transition_to(DeliveryStatus.DELIVERED)
    assert delivery.delivered_at is not None


def test_delivery_failed_can_only_be_cancelled() -> None:
    """Failed deliveries can be cancelled but not delivered."""
    delivery = _delivery(DeliveryStatus.FAILED)

    assert delivery.can_transition_to(DeliveryStatus.CANCELLED) is True
    assert delivery.can_transition_to(DeliveryStatus.DELIVERED) is False
    with pytest.raises(ValueError, match="Cannot transition from FAILED"):
        delivery.transition_to(DeliveryStatus.DELIVERED)


def test_promotion_validity() -> None:
    """Promotion validity depends on active flag, window, and usage limit."""
    now = datetime.utcnow()
    promotion = Promotion(
        restaurant_id=uuid.uuid4(),
        name="WELCOME",
        type=PromotionType.FIXED_AMOUNT,
        value=Decimal("10000"),
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=1),
    )

    assert promotion.is_valid(now) is True
    assert promotion.is_valid(now - timedelta(days=2)) is False
    assert promotion.is_valid(now + timedelta(days=2)) is False

    promotion.is_active = False
    assert promotion.is_valid(now) is False

    promotion.is_active = True
    promotion.usage_limit = 1
    promotion.usage_count = 1
    assert promotion.is_valid(now) is False


def test_domain_entity_validation() -> None:
    """Entities enforce field constraints."""
    with pytest.raises(ValidationError):
        _order().status = "UNKNOWN"  # type: ignore[assignment]
    with pytest.raises(ValidationError):
        Delivery(
            order_id=uuid.uuid4(),
            provider=DeliveryProvider.AHAMOVE,
            pickup_address=Address(street="", ward="W", district="D", city="C"),
            dropoff_address=address(),
            driver_phone=PhoneNumber(number="123"),
        )
