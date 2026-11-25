"""PaymentService tests."""

from __future__ import annotations

import uuid

import pytest

from app.domain.enums import PaymentMethod, PaymentStatus
from app.services.payment import PaymentService
from tests.factories import create_order, create_payment


async def test_create_payment_is_idempotent(session) -> None:
    """Creating a payment twice returns the existing payment."""
    order = await create_order(session)
    service = PaymentService(session)

    first = await service.create_payment(order_id=order.id, method=PaymentMethod.MOMO)
    second = await service.create_payment(order_id=order.id, method=PaymentMethod.MOMO)

    assert second.id == first.id
    assert first.status == PaymentStatus.PROCESSING
    assert first.provider_transaction_id == f"MOCK-PAY-{order.id.hex[:12].upper()}"


async def test_create_payment_missing_order_raises(session) -> None:
    """Creating a payment for an unknown order raises."""
    service = PaymentService(session)

    with pytest.raises(ValueError, match="Order not found"):
        await service.create_payment(order_id=uuid.uuid4(), method=PaymentMethod.CASH)


async def test_confirm_payment_success_and_idempotency(session) -> None:
    """Confirming a payment marks it completed and is idempotent."""
    order = await create_order(session)
    payment = await create_payment(session, order_id=order.id)
    service = PaymentService(session)

    confirmed = await service.confirm_payment(payment.id)
    assert confirmed.status == PaymentStatus.COMPLETED
    assert confirmed.paid_at is not None
    assert confirmed.provider_response == {"provider": "MOCK", "status": "COMPLETED"}

    again = await service.confirm_payment(payment.id)
    assert again.status == PaymentStatus.COMPLETED


async def test_confirm_payment_missing_transaction_id_raises(session) -> None:
    """Confirming a payment without a transaction id raises."""
    order = await create_order(session)
    payment = await create_payment(session, order_id=order.id, transaction_id=None)
    service = PaymentService(session)

    with pytest.raises(ValueError, match="Payment has no transaction ID"):
        await service.confirm_payment(payment.id)


async def test_refund_payment_success_and_validation(session) -> None:
    """Only completed payments can be refunded."""
    order = await create_order(session)
    processing = await create_payment(session, order_id=order.id)
    service = PaymentService(session)

    with pytest.raises(ValueError, match="Only completed payments can be refunded"):
        await service.refund_payment(processing.id)

    completed = await create_payment(
        session,
        order_id=(await create_order(session)).id,
        status=PaymentStatus.COMPLETED,
    )
    refunded = await service.refund_payment(completed.id)
    assert refunded.status == PaymentStatus.REFUNDED
    assert refunded.provider_response["status"] == "REFUNDED"


async def test_get_payment_by_order(session) -> None:
    """Payment lookup by order returns the payment or None."""
    order = await create_order(session)
    payment = await create_payment(session, order_id=order.id)
    service = PaymentService(session)

    fetched = await service.get_payment_by_order(order.id)
    assert fetched is not None and fetched.id == payment.id
    assert await service.get_payment_by_order(uuid.uuid4()) is None
