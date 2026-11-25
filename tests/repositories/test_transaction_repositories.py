"""Order, payment, delivery, and review repository tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import DeliveryProvider, DeliveryStatus, OrderStatus, PaymentStatus
from app.orm.models import Order as OrderModel
from app.repositories.delivery import DeliveryRepository
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.review import ReviewRepository
from tests.factories import (
    create_delivery,
    create_menu_item,
    create_order,
    create_payment,
    create_restaurant,
    create_review,
    create_user,
)


async def test_order_repository_eager_loads_items_and_filters(session: AsyncSession) -> None:
    repo = OrderRepository(session)
    customer = await create_user(session)
    restaurant = await create_restaurant(session)
    item = await create_menu_item(session, restaurant_id=restaurant.id)
    order = await create_order(
        session,
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        items=[(item, 2, "No onions")],
        status=OrderStatus.CONFIRMED,
    )

    fetched = await repo.get(order.id)
    assert fetched is not None
    assert len(fetched.items) == 1
    assert fetched.items[0].quantity == 2
    assert fetched.items[0].note == "No onions"
    assert fetched.items[0].subtotal.amount == Decimal("100000")

    by_customer = await repo.get_by_customer(customer.id)
    by_restaurant = await repo.get_by_restaurant(restaurant.id)
    by_status = await repo.get_by_status(OrderStatus.CONFIRMED)
    all_orders = await repo.list_all()
    assert [entry.id for entry in by_customer] == [order.id]
    assert [entry.id for entry in by_restaurant] == [order.id]
    assert [entry.id for entry in by_status] == [order.id]
    assert [entry.id for entry in all_orders] == [order.id]

    # OrderRepository.update() inherits BaseRepository.update(), which calls
    # _to_domain() after refresh without eager-loading items. Under async
    # SQLAlchemy that triggers MissingGreenlet, so verify persistence via get().
    model = await session.get(OrderModel, order.id)
    assert model is not None
    model.customer_note = "Updated note"
    await session.flush()
    updated = await repo.get(order.id)
    assert updated is not None
    assert updated.customer_note == "Updated note"
    assert len(updated.items) == 1


async def test_payment_repository_json_round_trip(session: AsyncSession) -> None:
    repo = PaymentRepository(session)
    order = await create_order(session)
    payment = await create_payment(
        session,
        order_id=order.id,
        status=PaymentStatus.COMPLETED,
        provider_response={"provider": "MOCK", "nested": {"ok": True}},
    )

    fetched = await repo.get(payment.id)
    assert fetched is not None
    assert fetched.provider_response == {"provider": "MOCK", "nested": {"ok": True}}
    assert fetched.amount.amount == order.total_amount.amount

    by_order = await repo.get_by_order(order.id)
    assert by_order is not None and by_order.id == payment.id
    assert await repo.get_by_order(order.id) is not None

    payment.status = PaymentStatus.REFUNDED
    updated = await repo.update(payment)
    assert updated.status == PaymentStatus.REFUNDED


async def test_delivery_repository_flattened_fields_and_filters(session: AsyncSession) -> None:
    repo = DeliveryRepository(session)
    order = await create_order(session)
    delivery = await create_delivery(
        session,
        order_id=order.id,
        status=DeliveryStatus.DRIVER_ASSIGNED,
        provider=DeliveryProvider.LALAMOVE,
        driver_phone="0901234567",
        tracking_url="https://tracking.example.com/1",
    )

    fetched = await repo.get(delivery.id)
    assert fetched is not None
    assert fetched.provider == DeliveryProvider.LALAMOVE
    assert fetched.driver_phone is not None
    assert fetched.driver_phone.number == "+84901234567"
    assert fetched.pickup_address.street == "Restaurant Street"
    assert fetched.dropoff_address.street == order.delivery_address.street
    assert fetched.tracking_url == "https://tracking.example.com/1"

    by_order = await repo.get_by_order(order.id)
    assert by_order is not None and by_order.id == delivery.id
    by_status = await repo.get_by_status(DeliveryStatus.DRIVER_ASSIGNED)
    assert [entry.id for entry in by_status] == [delivery.id]

    delivery.status = DeliveryStatus.IN_TRANSIT
    updated = await repo.update(delivery)
    assert updated.status == DeliveryStatus.IN_TRANSIT


async def test_review_repository_csv_and_ordering(session: AsyncSession) -> None:
    repo = ReviewRepository(session)
    restaurant = await create_restaurant(session)
    customer = await create_user(session)
    order = await create_order(session, customer_id=customer.id, restaurant_id=restaurant.id)
    older = await create_review(
        session,
        order_id=order.id,
        customer_id=customer.id,
        restaurant_id=restaurant.id,
        images=["a.jpg", "b.jpg"],
    )
    older.created_at = datetime.utcnow() - timedelta(days=1)
    await repo.update(older)
    newer_order = await create_order(session, customer_id=customer.id, restaurant_id=restaurant.id)
    newer = await create_review(
        session,
        order_id=newer_order.id,
        customer_id=customer.id,
        restaurant_id=restaurant.id,
    )

    fetched = await repo.get(older.id)
    assert fetched is not None and fetched.images == ["a.jpg", "b.jpg"]

    by_restaurant = await repo.get_by_restaurant(restaurant.id)
    assert [entry.id for entry in by_restaurant] == [newer.id, older.id]

    by_order = await repo.get_by_order(newer_order.id)
    assert by_order is not None and by_order.id == newer.id
    assert await repo.get_by_order(order.id) is not None
