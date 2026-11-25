"""OrderService tests."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.enums import MenuItemStatus, OrderStatus, PromotionType
from app.services.order import OrderService
from tests.factories import (
    create_menu_item,
    create_order,
    create_promotion,
    create_restaurant,
    create_user,
)
from tests.helpers import patch_order_repository_add


def _delivery_address() -> dict[str, object]:
    return {
        "street": "123 Main Street",
        "ward": "Ward 1",
        "district": "District 1",
        "city": "Ho Chi Minh City",
        "latitude": 10.0,
        "longitude": 106.0,
    }


async def test_create_order_success(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Create order calculates totals and persists items."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    restaurant = await create_restaurant(session)
    item = await create_menu_item(session, restaurant_id=restaurant.id, price=Decimal("50000"))
    service = OrderService(session)

    order = await service.create_order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        items=[{"menu_item_id": item.id, "quantity": 2, "special_instructions": "No onions"}],
        delivery_address=_delivery_address(),  # type: ignore[arg-type]
        notes="Leave at door",
    )

    assert order.status == OrderStatus.PENDING
    assert order.subtotal.amount == Decimal("100000")
    assert order.delivery_fee.amount == Decimal("30000")
    assert order.total_amount.amount == Decimal("130000")
    assert len(order.items) == 1
    assert order.items[0].note == "No onions"
    assert order.customer_note == "Leave at door"


async def test_create_order_restaurant_errors(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing and inactive restaurants are rejected."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    inactive = await create_restaurant(session, is_active=False)
    service = OrderService(session)

    with pytest.raises(ValueError, match="Restaurant not found"):
        await service.create_order(
            customer_id=customer.id,
            restaurant_id=uuid.uuid4(),
            items=[],
            delivery_address=_delivery_address(),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="Restaurant is not active"):
        await service.create_order(
            customer_id=customer.id,
            restaurant_id=inactive.id,
            items=[],
            delivery_address=_delivery_address(),  # type: ignore[arg-type]
        )


async def test_create_order_menu_item_errors(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing and unavailable menu items are rejected."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    restaurant = await create_restaurant(session)
    unavailable = await create_menu_item(session, restaurant_id=restaurant.id, status=MenuItemStatus.UNAVAILABLE)
    service = OrderService(session)

    with pytest.raises(ValueError, match="not found"):
        await service.create_order(
            customer_id=customer.id,
            restaurant_id=restaurant.id,
            items=[{"menu_item_id": uuid.uuid4(), "quantity": 1, "special_instructions": None}],
            delivery_address=_delivery_address(),  # type: ignore[arg-type]
        )

    with pytest.raises(ValueError, match="is not available"):
        await service.create_order(
            customer_id=customer.id,
            restaurant_id=restaurant.id,
            items=[{"menu_item_id": unavailable.id, "quantity": 1, "special_instructions": None}],
            delivery_address=_delivery_address(),  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("promotion_type", "value", "expected_discount"),
    [
        (PromotionType.FIXED_AMOUNT, Decimal("20000"), Decimal("20000")),
        (PromotionType.FREE_DELIVERY, Decimal("0"), Decimal("30000")),
    ],
)
async def test_create_order_applies_promotions(
    session,
    monkeypatch: pytest.MonkeyPatch,
    promotion_type: PromotionType,
    value: Decimal,
    expected_discount: Decimal,
) -> None:
    """Supported promotion types reduce the order total."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    restaurant = await create_restaurant(session)
    item = await create_menu_item(session, restaurant_id=restaurant.id, price=Decimal("100000"))
    await create_promotion(
        session,
        restaurant_id=restaurant.id,
        name="SAVE",
        type=promotion_type,
        value=value,
    )
    service = OrderService(session)

    order = await service.create_order(
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        items=[{"menu_item_id": item.id, "quantity": 1, "special_instructions": None}],
        delivery_address=_delivery_address(),  # type: ignore[arg-type]
        promotion_code="SAVE",
    )

    assert order.discount_amount.amount == expected_discount
    assert order.total_amount.amount == Decimal("100000") + Decimal("30000") - expected_discount
    assert order.promotion_code == "SAVE"


async def test_create_order_percentage_promotion_decimal_precision_bug(
    session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Percentage promotions currently fail because the discount has four decimals."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    restaurant = await create_restaurant(session)
    item = await create_menu_item(session, restaurant_id=restaurant.id, price=Decimal("100000"))
    await create_promotion(
        session,
        restaurant_id=restaurant.id,
        name="SAVE",
        type=PromotionType.PERCENTAGE,
        value=Decimal("10"),
    )
    service = OrderService(session)

    with pytest.raises(ValidationError, match="more than 2 decimal places"):
        await service.create_order(
            customer_id=customer.id,
            restaurant_id=restaurant.id,
            items=[{"menu_item_id": item.id, "quantity": 1, "special_instructions": None}],
            delivery_address=_delivery_address(),  # type: ignore[arg-type]
            promotion_code="SAVE",
        )


async def test_update_order_status_and_cancel(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid transitions update status; invalid transitions raise."""
    patch_order_repository_add(monkeypatch)
    order = await create_order(session, status=OrderStatus.CONFIRMED)
    service = OrderService(session)

    updated = await service.update_order_status(order.id, OrderStatus.PREPARING)
    assert updated.status == OrderStatus.PREPARING

    with pytest.raises(ValueError, match="Cannot transition"):
        await service.update_order_status(order.id, OrderStatus.DELIVERED)

    cancelled = await service.cancel_order(order.id, "Customer changed mind")
    assert cancelled.status == OrderStatus.CANCELLED
    assert cancelled.cancellation_reason == "Customer changed mind"


async def test_update_order_status_auto_dispatches(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reaching READY_FOR_PICKUP triggers delivery auto-dispatch."""
    patch_order_repository_add(monkeypatch)
    order = await create_order(session, status=OrderStatus.PREPARING)
    service = OrderService(session)
    dispatched: list[uuid.UUID] = []

    async def fake_auto_dispatch(self: object, order_id: uuid.UUID) -> None:
        dispatched.append(order_id)

    monkeypatch.setattr("app.services.order.DeliveryService.auto_dispatch", fake_auto_dispatch)

    updated = await service.update_order_status(order.id, OrderStatus.READY_FOR_PICKUP)

    assert updated.status == OrderStatus.READY_FOR_PICKUP
    assert dispatched == [order.id]


async def test_reorder_errors_and_success(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reorder validates ownership and delivered status."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    other = await create_user(session)
    restaurant = await create_restaurant(session)
    item = await create_menu_item(session, restaurant_id=restaurant.id)
    delivered = await create_order(
        session,
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        items=[(item, 1, None)],
        status=OrderStatus.DELIVERED,
    )
    pending = await create_order(session, customer_id=customer.id, restaurant_id=restaurant.id)
    service = OrderService(session)

    with pytest.raises(ValueError, match="Original order not found"):
        await service.reorder(uuid.uuid4(), customer.id)

    with pytest.raises(ValueError, match="does not belong"):
        await service.reorder(delivered.id, other.id)

    with pytest.raises(ValueError, match="Can only reorder delivered orders"):
        await service.reorder(pending.id, customer.id)

    reordered = await service.reorder(delivered.id, customer.id)
    assert reordered.id != delivered.id
    assert reordered.customer_id == customer.id
    assert reordered.restaurant_id == restaurant.id
    assert len(reordered.items) == 1
