"""ReviewService tests."""

from __future__ import annotations

import uuid

import pytest

from app.domain.enums import OrderStatus
from app.services.review import ReviewService
from tests.factories import create_order, create_restaurant, create_review, create_user
from tests.helpers import patch_order_repository_add


async def test_create_review_success(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """A delivered order can be reviewed once."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    restaurant = await create_restaurant(session)
    order = await create_order(
        session,
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        status=OrderStatus.DELIVERED,
    )
    service = ReviewService(session)

    review = await service.create_review(
        order_id=order.id,
        customer_id=customer.id,
        rating=5,
        comment="Great food",
        images=["a.jpg"],
    )

    assert review.order_id == order.id
    assert review.restaurant_id == restaurant.id
    assert review.rating == 5
    assert review.images == ["a.jpg"]

    with pytest.raises(ValueError, match="Review already exists"):
        await service.create_review(
            order_id=order.id,
            customer_id=customer.id,
            rating=4,
        )


async def test_create_review_validation(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review creation validates order existence, ownership, and status."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    other = await create_user(session)
    delivered = await create_order(session, customer_id=customer.id, status=OrderStatus.DELIVERED)
    pending = await create_order(session, customer_id=customer.id, status=OrderStatus.PENDING)
    service = ReviewService(session)

    with pytest.raises(ValueError, match="Order not found"):
        await service.create_review(order_id=uuid.uuid4(), customer_id=customer.id, rating=5)

    with pytest.raises(ValueError, match="does not belong"):
        await service.create_review(order_id=delivered.id, customer_id=other.id, rating=5)

    with pytest.raises(ValueError, match="Can only review delivered orders"):
        await service.create_review(order_id=pending.id, customer_id=customer.id, rating=5)


async def test_review_lookup_helpers(session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Review lookup by restaurant and order works."""
    patch_order_repository_add(monkeypatch)
    customer = await create_user(session)
    restaurant = await create_restaurant(session)
    order = await create_order(
        session,
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        status=OrderStatus.DELIVERED,
    )
    review = await create_review(
        session,
        order_id=order.id,
        customer_id=customer.id,
        restaurant_id=restaurant.id,
    )
    service = ReviewService(session)

    by_restaurant = await service.get_restaurant_reviews(restaurant.id)
    by_order = await service.get_order_review(order.id)
    assert [entry.id for entry in by_restaurant] == [review.id]
    assert by_order is not None and by_order.id == review.id
    assert await service.get_order_review(uuid.uuid4()) is None
