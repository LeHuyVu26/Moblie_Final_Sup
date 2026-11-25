"""DeliveryService tests."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.adapters.delivery import DeliveryBooking
from app.domain.enums import DeliveryProvider, DeliveryStatus, OrderStatus
from app.domain.value_objects import Address, Coordinates
from app.services.delivery import DeliveryService
from tests.factories import create_delivery, create_order, create_restaurant
from tests.helpers import patch_order_repository_add


async def test_get_quote_returns_mock_pricing(session) -> None:
    """Quote uses distance-based mock pricing."""
    service = DeliveryService(session)
    pickup = Address(street="A", ward="W", district="D", city="C")
    dropoff = Address(street="B", ward="W", district="D", city="C")

    quote = await service.get_quote(
        pickup=pickup,
        dropoff=dropoff,
        pickup_coordinates=Coordinates(latitude=10.0, longitude=106.0),
        dropoff_coordinates=Coordinates(latitude=10.0, longitude=106.0),
    )

    assert quote["provider"] == DeliveryProvider.AHAMOVE.value
    assert quote["fee"] == Decimal("15000")
    assert quote["distance_km"] == Decimal("0.0")
    assert quote["estimated_duration_minutes"] == 10


async def test_auto_dispatch_creates_delivery(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-dispatch books a delivery for a ready order."""
    patch_order_repository_add(monkeypatch)
    restaurant = await create_restaurant(session)
    order = await create_order(
        session,
        restaurant_id=restaurant.id,
        status=OrderStatus.READY_FOR_PICKUP,
    )
    service = DeliveryService(session)

    delivery = await service.auto_dispatch(order.id)

    assert delivery.order_id == order.id
    assert delivery.status == DeliveryStatus.DRIVER_ASSIGNED
    assert delivery.provider_order_id is not None
    assert delivery.provider_order_id.startswith("MOCK-AHAMOVE-")
    assert delivery.driver_phone is not None
    assert delivery.driver_phone.number == "+84901234567"
    assert delivery.tracking_url is not None

    again = await service.auto_dispatch(order.id)
    assert again.id == delivery.id


async def test_auto_dispatch_validation(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Auto-dispatch validates order state."""
    patch_order_repository_add(monkeypatch)
    order = await create_order(session, status=OrderStatus.PENDING)
    service = DeliveryService(session)

    with pytest.raises(ValueError, match="Order not found"):
        await service.auto_dispatch(uuid.uuid4())

    with pytest.raises(ValueError, match="Order is not ready for pickup"):
        await service.auto_dispatch(order.id)


async def test_auto_dispatch_uses_booking_status(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Booking status is copied directly onto the delivery."""
    patch_order_repository_add(monkeypatch)
    order = await create_order(session, status=OrderStatus.READY_FOR_PICKUP)
    service = DeliveryService(session)

    async def fake_booking(**_kwargs: object) -> DeliveryBooking:
        return DeliveryBooking(
            provider_order_id="BOOK-1",
            status=DeliveryStatus.IN_TRANSIT,
            driver_name="Tester",
        )

    class FakeAdapter:
        async def get_quote(self, **_kwargs: object) -> None:
            return None

        async def create_booking(self, **kwargs: object) -> DeliveryBooking:
            return await fake_booking(**kwargs)

    monkeypatch.setattr("app.services.delivery.get_delivery_adapter", lambda *_: FakeAdapter())

    delivery = await service.auto_dispatch(order.id)
    assert delivery.status == DeliveryStatus.IN_TRANSIT
    assert delivery.provider_order_id == "BOOK-1"
    assert delivery.driver_name == "Tester"


async def test_update_delivery_status_and_tracking(session) -> None:
    """Delivery status transitions and tracking updates work."""
    order = await create_order(session)
    delivery = await create_delivery(session, order_id=order.id)
    service = DeliveryService(session)

    assigned = await service.update_delivery_status(delivery.id, DeliveryStatus.DRIVER_ASSIGNED)
    assert assigned.status == DeliveryStatus.DRIVER_ASSIGNED

    tracked = await service.update_tracking(
        order.id,
        status=DeliveryStatus.DRIVER_EN_ROUTE_TO_PICKUP,
        driver_name="New Driver",
        driver_phone="0912345678",
        tracking_url="https://tracking.example.com/new",
    )
    assert tracked.status == DeliveryStatus.DRIVER_EN_ROUTE_TO_PICKUP
    assert tracked.driver_name == "New Driver"
    assert tracked.driver_phone is not None
    assert tracked.driver_phone.number == "+84912345678"
    assert tracked.tracking_url == "https://tracking.example.com/new"

    with pytest.raises(ValueError, match="Cannot transition"):
        await service.update_delivery_status(delivery.id, DeliveryStatus.DELIVERED)


async def test_delivery_lookup_helpers(session) -> None:
    """Delivery lookup by id and order works."""
    order = await create_order(session)
    delivery = await create_delivery(session, order_id=order.id)
    service = DeliveryService(session)

    by_id = await service.get_delivery(delivery.id)
    by_order = await service.get_delivery_by_order(order.id)
    assert by_id is not None and by_id.id == delivery.id
    assert by_order is not None and by_order.id == delivery.id
    assert await service.get_delivery(uuid.uuid4()) is None
