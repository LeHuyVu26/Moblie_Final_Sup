"""Order endpoint tests."""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from app.domain.enums import OrderStatus
from tests.factories import create_menu_item, create_order, create_restaurant, create_user
from tests.helpers import assert_error, assert_page, assert_requires_auth, patch_order_repository_add


def _order_payload(restaurant_id: uuid.UUID, item_id: uuid.UUID) -> dict[str, object]:
    return {
        "restaurant_id": str(restaurant_id),
        "items": [{"menu_item_id": str(item_id), "quantity": 2, "special_instructions": "No onions"}],
        "delivery_address": {
            "street": "123 Main Street",
            "ward": "Ward 1",
            "district": "District 1",
            "city": "Ho Chi Minh City",
            "latitude": "10.0",
            "longitude": "106.0",
        },
        "notes": "Leave at door",
    }


async def test_create_get_and_list_orders(
    client_factory, session, customer_user, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Customers can create, fetch, and list their orders."""
    patch_order_repository_add(monkeypatch)
    restaurant = await create_restaurant(session)
    item = await create_menu_item(session, restaurant_id=restaurant.id, price="50000")  # type: ignore[arg-type]

    async with client_factory(customer_user) as client:
        created = await client.post("/v1/order/", json=_order_payload(restaurant.id, item.id))
        assert created.status_code == 200
        body = created.json()
        order_id = body["id"]
        assert body["status"] == "PENDING"
        assert body["payment_status"] == "PENDING"
        assert body["restaurant_name"] == restaurant.name
        assert Decimal(body["subtotal"]) == Decimal("100000")
        assert Decimal(body["delivery_fee"]) == Decimal("30000")
        assert Decimal(body["total_amount"]) == Decimal("130000")
        assert body["notes"] == "Leave at door"
        assert body["items"][0]["special_instructions"] == "No onions"

        fetched = await client.get(f"/v1/order/{order_id}")
        assert fetched.status_code == 200
        assert fetched.json()["id"] == order_id

        listed = await client.get("/v1/order/")
        assert listed.status_code == 200
        assert [entry["id"] for entry in assert_page(listed.json())] == [order_id]


async def test_create_order_validation(client_factory, session, customer_user) -> None:
    """Order creation maps service errors to 400."""
    async with client_factory(customer_user) as client:
        missing = await client.post("/v1/order/", json=_order_payload(uuid.uuid4(), uuid.uuid4()))
        assert_error(missing, 400, "Restaurant not found")


async def test_get_order_access_control(client_factory, session, customer_user) -> None:
    """Customers cannot read another customer's order."""
    other = await create_user(session)
    order = await create_order(session, customer_id=other.id)

    async with client_factory(customer_user) as client:
        forbidden = await client.get(f"/v1/order/{order.id}")
        assert_error(forbidden, 403, "Not allowed")

        missing = await client.get(f"/v1/order/{uuid.uuid4()}")
        assert_error(missing, 404, "Order not found")

    async with client_factory(None) as client:
        await assert_requires_auth(client, "GET", f"/v1/order/{order.id}")


async def test_update_order_status(
    client_factory, session, owner_user, customer_user, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Owners can update valid order statuses."""
    patch_order_repository_add(monkeypatch)
    order = await create_order(session, status=OrderStatus.PENDING)

    async with client_factory(owner_user) as client:
        updated = await client.patch(f"/v1/order/{order.id}/status", json={"status": "CONFIRMED", "reason": "Accepted"})
        assert updated.status_code == 200
        assert updated.json()["status"] == "CONFIRMED"

        invalid = await client.patch(f"/v1/order/{order.id}/status", json={"status": "DELIVERED"})
        assert_error(invalid, 400, "Cannot transition from CONFIRMED to OrderStatus.DELIVERED")

    async with client_factory(customer_user) as client:
        forbidden = await client.patch(f"/v1/order/{order.id}/status", json={"status": "PREPARING"})
        assert_error(forbidden, 403, "Not allowed")


async def test_reorder(client_factory, session, customer_user, monkeypatch: pytest.MonkeyPatch) -> None:
    """Customers can reorder delivered orders."""
    patch_order_repository_add(monkeypatch)
    restaurant = await create_restaurant(session)
    item = await create_menu_item(session, restaurant_id=restaurant.id)
    delivered = await create_order(
        session,
        customer_id=customer_user.id,
        restaurant_id=restaurant.id,
        items=[(item, 1, None)],
        status=OrderStatus.DELIVERED,
    )
    pending = await create_order(session, customer_id=customer_user.id, restaurant_id=restaurant.id)

    async with client_factory(customer_user) as client:
        reordered = await client.post(f"/v1/order/{delivered.id}/reorder")
        assert reordered.status_code == 200
        assert reordered.json()["id"] != str(delivered.id)
        assert reordered.json()["status"] == "PENDING"

        invalid = await client.post(f"/v1/order/{pending.id}/reorder")
        assert_error(invalid, 400, "Can only reorder delivered orders")
