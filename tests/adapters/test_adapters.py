"""Tests for deterministic mock external providers."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.adapters.delivery import (
    DeliveryBooking,
    DeliveryQuote,
    MockDeliveryAdapter,
    get_delivery_adapter,
)
from app.adapters.notification import (
    MockNotificationAdapter,
    NotificationResult,
    get_notification_adapter,
)
from app.adapters.payment import MockPaymentAdapter, PaymentResult, get_payment_adapter
from app.domain.enums import (
    DeliveryProvider,
    DeliveryStatus,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.domain.value_objects import Address, Coordinates
from tests.factories import address


async def test_delivery_quote_uses_coordinates_when_available() -> None:
    """Quote computes distance-based fee and duration."""
    adapter = MockDeliveryAdapter(DeliveryProvider.LALAMOVE)
    pickup = address(latitude=10.0, longitude=106.0)
    dropoff = address(latitude=10.1, longitude=106.0)

    quote = await adapter.get_quote(
        pickup=pickup,
        dropoff=dropoff,
        pickup_coordinates=Coordinates(latitude=10.0, longitude=106.0),
        dropoff_coordinates=Coordinates(latitude=10.1, longitude=106.0),
    )

    assert isinstance(quote, DeliveryQuote)
    assert quote.provider == DeliveryProvider.LALAMOVE
    assert quote.distance_km == Decimal("11.1")
    assert quote.fee == Decimal("70597")
    assert quote.estimated_duration_minutes == 65


async def test_delivery_quote_uses_default_distance() -> None:
    """Quote falls back to 3km when coordinates are missing."""
    adapter = MockDeliveryAdapter(DeliveryProvider.AHAMOVE)
    pickup = Address(street="A", ward="W", district="D", city="C")
    dropoff = Address(street="B", ward="W", district="D", city="C")

    quote = await adapter.get_quote(pickup=pickup, dropoff=dropoff)

    assert quote.distance_km == Decimal("3.0")
    assert quote.fee == Decimal("30000")
    assert quote.estimated_duration_minutes == 25


async def test_delivery_booking_is_deterministic() -> None:
    """Booking IDs and driver details are deterministic."""
    adapter = MockDeliveryAdapter(DeliveryProvider.AHAMOVE)
    order_id = uuid.UUID("12345678-1234-5678-1234-567812345678")

    booking = await adapter.create_booking(
        order_id=order_id,
        pickup=address(),
        dropoff=address(),
        cod_amount=Decimal("99000"),
        notes="Ring the bell",
    )

    assert isinstance(booking, DeliveryBooking)
    assert booking.provider_order_id == "MOCK-AHAMOVE-123456781234"
    assert booking.status == DeliveryStatus.DRIVER_ASSIGNED
    assert booking.driver_name == "Nguyễn Văn A (Mock)"
    assert booking.driver_phone == "0901234567"
    assert booking.driver_vehicle == "Xe máy"
    assert booking.driver_license_plate == "51B-12345"
    assert booking.tracking_url == f"https://tracking.mock.com/ahamove/{order_id}"


def test_delivery_adapter_factory() -> None:
    """Delivery adapter factory returns the mock adapter."""
    adapter = get_delivery_adapter(DeliveryProvider.LALAMOVE)
    assert isinstance(adapter, MockDeliveryAdapter)
    assert adapter.provider == DeliveryProvider.LALAMOVE


async def test_payment_adapter_results() -> None:
    """Payment adapter returns deterministic mock results."""
    adapter = MockPaymentAdapter()
    order_id = uuid.UUID("12345678-1234-5678-1234-567812345678")

    created = await adapter.create_payment(order_id=order_id, amount=Decimal("99000"), method=PaymentMethod.MOMO)
    assert isinstance(created, PaymentResult)
    assert created.transaction_id == "MOCK-PAY-123456781234"
    assert created.status == PaymentStatus.PROCESSING
    assert created.provider_response["method"] == "MOMO"
    assert created.provider_response["amount"] == "99000"

    confirmed = await adapter.confirm_payment(transaction_id=created.transaction_id)
    assert confirmed.status == PaymentStatus.COMPLETED
    assert confirmed.provider_response == {"provider": "MOCK", "status": "COMPLETED"}

    refunded = await adapter.refund_payment(transaction_id=created.transaction_id, amount=Decimal("99000"))
    assert refunded.status == PaymentStatus.REFUNDED
    assert refunded.provider_response["amount"] == "99000"


def test_payment_adapter_factory() -> None:
    """Payment adapter factory returns the mock adapter."""
    assert isinstance(get_payment_adapter(), MockPaymentAdapter)


async def test_notification_adapter_results() -> None:
    """Notification adapter returns deterministic mock message IDs."""
    adapter = MockNotificationAdapter()
    user_id = uuid.uuid4()
    order_id = uuid.UUID("12345678-1234-5678-1234-567812345678")

    order_notification = await adapter.send_order_status(
        user_id=user_id, order_id=order_id, status=OrderStatus.CONFIRMED
    )
    assert isinstance(order_notification, NotificationResult)
    assert order_notification.success is True
    assert order_notification.message_id == "MOCK-ORDER-123456781234-CONFIRMED"

    delivery_notification = await adapter.send_delivery_status(
        user_id=user_id, order_id=order_id, status=DeliveryStatus.IN_TRANSIT
    )
    assert delivery_notification.success is True
    assert delivery_notification.message_id == "MOCK-DELIVERY-123456781234-IN_TRANSIT"


def test_notification_adapter_factory() -> None:
    """Notification adapter factory returns the mock adapter."""
    assert isinstance(get_notification_adapter(), MockNotificationAdapter)
