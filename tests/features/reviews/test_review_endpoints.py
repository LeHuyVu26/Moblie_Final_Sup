"""Review endpoint tests."""

from __future__ import annotations

import uuid

from app.domain.enums import OrderStatus
from tests.factories import create_order, create_restaurant, create_user
from tests.helpers import assert_error, assert_page, assert_requires_auth


async def test_create_and_list_reviews(client_factory, session, customer_user) -> None:
    """Customers can review delivered orders and list restaurant reviews."""
    restaurant = await create_restaurant(session)
    order = await create_order(
        session,
        customer_id=customer_user.id,
        restaurant_id=restaurant.id,
        status=OrderStatus.DELIVERED,
    )

    async with client_factory(customer_user) as client:
        created = await client.post(
            f"/v1/review/{order.id}/reviews",
            json={"rating": 5, "comment": "Great food", "images": ["a.jpg"]},
        )
        assert created.status_code == 200
        body = created.json()
        assert body["order_id"] == str(order.id)
        assert body["restaurant_id"] == str(restaurant.id)
        assert body["customer_id"] == str(customer_user.id)
        assert body["rating"] == 5
        assert body["images"] == ["a.jpg"]
        assert body["customer_name"] == ""

        duplicate = await client.post(f"/v1/review/{order.id}/reviews", json={"rating": 4})
        assert_error(duplicate, 400, "Review already exists for this order")

        listed = await client.get(f"/v1/review/restaurants/{restaurant.id}/reviews")
        assert listed.status_code == 200
        assert [item["id"] for item in assert_page(listed.json())] == [body["id"]]


async def test_review_validation(client_factory, session, customer_user) -> None:
    """Review creation validates order existence, ownership, and status."""
    other = await create_user(session)
    delivered = await create_order(session, customer_id=other.id, status=OrderStatus.DELIVERED)
    pending = await create_order(session, customer_id=customer_user.id)

    async with client_factory(customer_user) as client:
        missing = await client.post(f"/v1/review/{uuid.uuid4()}/reviews", json={"rating": 5})
        assert_error(missing, 400, "Order not found")

        not_owner = await client.post(f"/v1/review/{delivered.id}/reviews", json={"rating": 5})
        assert_error(not_owner, 400, "Order does not belong to this customer")

        not_delivered = await client.post(f"/v1/review/{pending.id}/reviews", json={"rating": 5})
        assert_error(not_delivered, 400, "Can only review delivered orders")

        invalid_rating = await client.post(f"/v1/review/{pending.id}/reviews", json={"rating": 6})
        assert invalid_rating.status_code == 422

    async with client_factory(None) as client:
        await assert_requires_auth(client, "POST", f"/v1/review/{pending.id}/reviews", json={"rating": 5})
