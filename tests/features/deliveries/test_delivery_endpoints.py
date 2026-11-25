"""Delivery endpoint tests."""

from __future__ import annotations

import uuid

from app.domain.enums import DeliveryStatus, OrderStatus
from tests.factories import create_delivery, create_order
from tests.helpers import assert_error, assert_requires_auth


async def test_dispatch_get_and_track_delivery(client_factory, session, owner_user, customer_user) -> None:
    """Owners can dispatch deliveries and tracking can be updated."""
    order = await create_order(session, customer_id=customer_user.id, status=OrderStatus.READY_FOR_PICKUP)

    async with client_factory(owner_user) as client:
        dispatched = await client.post(f"/v1/delivery/{order.id}/delivery/dispatch", json={"provider": "AHAMOVE"})
        assert dispatched.status_code == 200
        body = dispatched.json()
        assert body["order_id"] == str(order.id)
        assert body["status"] == "DRIVER_ASSIGNED"
        assert body["provider"] == "AHAMOVE"
        assert body["driver_phone"] == "+84901234567"

        fetched = await client.get(f"/v1/delivery/{order.id}/delivery")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == body["id"]

        tracked = await client.patch(
            f"/v1/delivery/{order.id}/delivery/tracking",
            json={
                "status": "DRIVER_EN_ROUTE_TO_PICKUP",
                "driver_name": "Updated Driver",
                "driver_phone": "0912345678",
                "tracking_url": "https://tracking.example.com/updated",
            },
        )
        assert tracked.status_code == 200
        assert tracked.json()["status"] == "DRIVER_EN_ROUTE_TO_PICKUP"
        assert tracked.json()["driver_name"] == "Updated Driver"
        assert tracked.json()["driver_phone"] == "+84912345678"


async def test_delivery_errors(client_factory, session, owner_user, customer_user) -> None:
    """Delivery endpoints validate role and state."""
    pending_order = await create_order(session, customer_id=customer_user.id)
    delivered_order = await create_order(session, customer_id=customer_user.id)
    delivery = await create_delivery(session, order_id=delivered_order.id)

    async with client_factory(customer_user) as client:
        forbidden = await client.post(
            f"/v1/delivery/{pending_order.id}/delivery/dispatch", json={"provider": "AHAMOVE"}
        )
        assert_error(forbidden, 403, "Not allowed")

    async with client_factory(owner_user) as client:
        not_ready = await client.post(
            f"/v1/delivery/{pending_order.id}/delivery/dispatch", json={"provider": "AHAMOVE"}
        )
        assert_error(not_ready, 400, "Order is not ready for pickup")

        missing = await client.get(f"/v1/delivery/{uuid.uuid4()}/delivery")
        assert_error(missing, 404, "Delivery not found")

        invalid_tracking = await client.patch(
            f"/v1/delivery/{delivered_order.id}/delivery/tracking",
            json={"status": "DELIVERED"},
        )
        assert_error(
            invalid_tracking,
            400,
            "Cannot transition from PENDING_DISPATCH to DeliveryStatus.DELIVERED",
        )

    assert delivery.status == DeliveryStatus.PENDING_DISPATCH

    async with client_factory(None) as client:
        await assert_requires_auth(client, "GET", f"/v1/delivery/{delivered_order.id}/delivery")
