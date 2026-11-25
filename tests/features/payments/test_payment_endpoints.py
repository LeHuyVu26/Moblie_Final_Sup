"""Payment endpoint tests."""

from __future__ import annotations

import uuid

from tests.factories import create_order, create_payment
from tests.helpers import assert_error, assert_requires_auth


async def test_payment_lifecycle(client_factory, session, customer_user) -> None:
    """Payments can be created, fetched, confirmed, and refunded."""
    order = await create_order(session, customer_id=customer_user.id)

    async with client_factory(customer_user) as client:
        created = await client.post(f"/v1/payment/{order.id}/payments", json={"method": "MOMO"})
        assert created.status_code == 200
        payment_id = created.json()["id"]
        assert created.json()["status"] == "PROCESSING"
        assert created.json()["method"] == "MOMO"
        assert created.json()["transaction_id"] == f"MOCK-PAY-{order.id.hex[:12].upper()}"

        fetched = await client.get(f"/v1/payment/{order.id}/payments")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == payment_id

        confirmed = await client.post(f"/v1/payment/payments/{payment_id}/confirm")
        assert confirmed.status_code == 200
        assert confirmed.json()["status"] == "COMPLETED"
        assert confirmed.json()["paid_at"] is not None

        refunded = await client.post(f"/v1/payment/payments/{payment_id}/refund")
        assert refunded.status_code == 200
        assert refunded.json()["status"] == "REFUNDED"


async def test_payment_errors(client_factory, session, customer_user) -> None:
    """Payment endpoints map service errors to HTTP errors."""
    order = await create_order(session, customer_id=customer_user.id)
    processing = await create_payment(session, order_id=order.id)

    async with client_factory(customer_user) as client:
        missing_order = await client.post(f"/v1/payment/{uuid.uuid4()}/payments", json={"method": "CASH"})
        assert_error(missing_order, 400, "Order not found")

        missing_payment = await client.get(f"/v1/payment/{uuid.uuid4()}/payments")
        assert_error(missing_payment, 404, "Payment not found")

        invalid_refund = await client.post(f"/v1/payment/payments/{processing.id}/refund")
        assert_error(invalid_refund, 400, "Only completed payments can be refunded")

    async with client_factory(None) as client:
        await assert_requires_auth(client, "GET", f"/v1/payment/{order.id}/payments")
