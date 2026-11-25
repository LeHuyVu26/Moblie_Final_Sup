"""Domain-to-API mapper tests."""

from __future__ import annotations

from decimal import Decimal

from app.api.mappers import (
    map_category,
    map_delivery,
    map_menu_item,
    map_order,
    map_order_summary,
    map_page,
    map_payment,
    map_promotion,
    map_restaurant,
    map_restaurant_summary,
    map_review,
    map_user,
    map_user_profile,
)
from app.domain.enums import DiscountType, PaymentMethod, PaymentStatus, RestaurantStatus
from tests.factories import (
    create_category,
    create_delivery,
    create_menu_item,
    create_order,
    create_payment,
    create_promotion,
    create_restaurant,
    create_review,
    create_user,
)


async def test_map_user(session) -> None:
    """User mappers expose the same public fields."""
    user = await create_user(session, full_name="Test User")

    response = map_user(user)
    profile = map_user_profile(user)

    assert response.id == user.id
    assert response.phone == user.phone.number
    assert response.full_name == "Test User"
    assert profile.email == user.email
    assert profile.role == user.role


async def test_map_restaurant(session) -> None:
    """Restaurant mappers flatten address and derive status."""
    restaurant = await create_restaurant(session, delivery_fee=Decimal("30000"))

    response = map_restaurant(restaurant)
    summary = map_restaurant_summary(restaurant)

    assert response.street == restaurant.address.street
    assert response.latitude == Decimal("10.0")
    assert response.delivery_fee == Decimal("30000.00")
    assert response.status == RestaurantStatus.ACTIVE
    assert response.opening_time.isoformat() == "08:00:00"
    assert summary.id == restaurant.id
    assert summary.status == RestaurantStatus.ACTIVE

    inactive = restaurant.model_copy(update={"is_active": False})
    assert map_restaurant(inactive).status == RestaurantStatus.SUSPENDED


async def test_map_category_and_menu_item(session) -> None:
    """Catalog mappers preserve identifiers and money values."""
    restaurant = await create_restaurant(session)
    category = await create_category(session, restaurant_id=restaurant.id)
    item = await create_menu_item(
        session,
        restaurant_id=restaurant.id,
        category_id=category.id,
        price=Decimal("50000"),
        original_price=Decimal("45000"),
    )

    category_response = map_category(category)
    item_response = map_menu_item(item)

    assert category_response.restaurant_id == restaurant.id
    assert item_response.category_id == category.id
    assert item_response.price == Decimal("50000.00")
    assert item_response.discounted_price == Decimal("45000.00")
    assert item_response.is_featured is False


async def test_map_promotion_and_fallback(session) -> None:
    """Promotion mapper maps names to codes and falls back for unknown types."""
    promotion = await create_promotion(session, name="WELCOME")

    response = map_promotion(promotion)

    assert response.code == "WELCOME"
    assert response.title == "WELCOME"
    assert response.discount_type == DiscountType.PERCENTAGE
    assert response.minimum_order_amount == Decimal("0")
    assert response.applicable_item_ids == []

    unknown = promotion.model_copy(update={"type": "UNKNOWN"})
    assert map_promotion(unknown).discount_type == DiscountType.FIXED_AMOUNT


async def test_map_order_and_summary(session) -> None:
    """Order mappers include items, totals, and address details."""
    order = await create_order(session, customer_note="Leave at door")

    response = map_order(order, restaurant_name="Test Restaurant", payment_status=PaymentStatus.COMPLETED)
    summary = map_order_summary(order, restaurant_name="Test Restaurant")

    assert response.restaurant_name == "Test Restaurant"
    assert response.payment_status == PaymentStatus.COMPLETED
    assert len(response.items) == 1
    assert response.items[0].subtotal == Decimal("50000.00")
    assert response.total_amount == Decimal("80000.00")
    assert response.delivery_address.latitude == Decimal("10.0")
    assert response.notes == "Leave at door"
    assert response.scheduled_for is None
    assert summary.total_amount == Decimal("80000.00")


async def test_map_payment_and_fallback(session) -> None:
    """Payment mapper maps provider to method with a cash fallback."""
    order = await create_order(session)
    payment = await create_payment(session, order_id=order.id)

    response = map_payment(payment)

    assert response.method == PaymentMethod.MOMO
    assert response.amount == order.total_amount.amount
    assert response.transaction_id == "MOCK-TXN-123"

    unknown = payment.model_copy(update={"provider": "UNKNOWN"})
    assert map_payment(unknown).method == PaymentMethod.CASH


async def test_map_delivery(session) -> None:
    """Delivery mapper flattens addresses and leaves estimates empty."""
    order = await create_order(session)
    delivery = await create_delivery(session, order_id=order.id, tracking_url="https://tracking.mock")

    response = map_delivery(delivery)

    assert response.order_id == order.id
    assert response.tracking_url == "https://tracking.mock"
    assert response.pickup_address.street == "Restaurant Street"
    assert response.dropoff_address.street == delivery.dropoff_address.street
    assert response.fee == Decimal("30000.00")
    assert response.estimated_pickup_at is None
    assert response.estimated_dropoff_at is None


async def test_map_review(session) -> None:
    """Review mapper accepts an optional customer name."""
    order = await create_order(session)
    review = await create_review(
        session,
        order_id=order.id,
        customer_id=order.customer_id,
        restaurant_id=order.restaurant_id,
    )

    response = map_review(review, customer_name="Customer")

    assert response.customer_name == "Customer"
    assert response.rating == 5
    assert response.comment == "Great food"
    assert map_review(review).customer_name == ""


def test_map_page() -> None:
    """Page mapper computes total page count."""
    page = map_page([1, 2, 3], total=7, page=2, size=3)

    assert page.items == [1, 2, 3]
    assert page.total == 7
    assert page.pages == 3
    assert map_page([], total=0, page=1, size=0).pages == 0
