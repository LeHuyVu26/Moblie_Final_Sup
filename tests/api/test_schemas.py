"""API schema validation tests."""

from __future__ import annotations

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api.schemas.auth import ChangePasswordRequest, LoginRequest, RegisterRequest
from app.api.schemas.common import ErrorResponse, Page
from app.api.schemas.deliveries import DeliveryDispatchRequest, DeliveryTrackingUpdate
from app.api.schemas.menu_items import MenuItemCreate
from app.api.schemas.orders import OrderCreate, OrderItemCreate, OrderStatusUpdate
from app.api.schemas.promotions import PromotionCreate
from app.api.schemas.restaurants import RestaurantCreate
from app.api.schemas.reviews import ReviewCreate
from app.domain.enums import (
    DeliveryProvider,
    DeliveryStatus,
    DiscountType,
    MenuItemStatus,
    OrderStatus,
    PromotionStatus,
    RestaurantStatus,
    UserRole,
)


def _order_address() -> dict[str, object]:
    return {
        "street": "123 Main Street",
        "ward": "Ward 1",
        "district": "District 1",
        "city": "Ho Chi Minh City",
    }


def test_register_request_validation() -> None:
    """Registration requires valid contact details and a strong password."""
    request = RegisterRequest(
        email="user@example.com",
        phone="0912345678",
        password="Password123",
        full_name="Test User",
    )

    assert request.role == UserRole.CUSTOMER

    with pytest.raises(ValidationError):
        RegisterRequest(email="invalid", phone="0912345678", password="Password123", full_name="Test User")
    with pytest.raises(ValidationError):
        RegisterRequest(email="user@example.com", phone="0912345678", password="short", full_name="Test User")
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            phone="0912345678",
            password="Password123",
            full_name="Test User",
            unexpected=True,  # type: ignore[call-arg]
        )


def test_login_and_password_change_requests() -> None:
    """Auth requests enforce minimum password lengths."""
    assert LoginRequest(email="user@example.com", password="x").password == "x"

    with pytest.raises(ValidationError):
        ChangePasswordRequest(current_password="Password123", new_password="short")


def test_common_schemas() -> None:
    """Common schemas reject extra fields."""
    page: Page[int] = Page[int](items=[1], total=1, page=1, size=20, pages=1)

    assert page.items == [1]
    assert ErrorResponse(detail="Not found").code is None
    with pytest.raises(ValidationError):
        ErrorResponse(detail="Not found", unexpected=True)  # type: ignore[call-arg]


def test_restaurant_create_validation() -> None:
    """Restaurant schemas validate radius and time formats."""
    request = RestaurantCreate(
        name="Test Restaurant",
        street="123 Main Street",
        ward="Ward 1",
        district="District 1",
        city="Ho Chi Minh City",
        phone="0912345678",
        opening_time=time(8, 0),
        closing_time=time(22, 0),
        delivery_radius_km=Decimal("5.0"),
        minimum_order_amount=Decimal("0"),
        delivery_fee=Decimal("30000"),
    )

    assert request.status == RestaurantStatus.PENDING

    with pytest.raises(ValidationError):
        RestaurantCreate(
            name="Test Restaurant",
            street="123 Main Street",
            ward="Ward 1",
            district="District 1",
            city="Ho Chi Minh City",
            phone="0912345678",
            opening_time=time(8, 0),
            closing_time=time(22, 0),
            delivery_radius_km=Decimal("0.01"),
            minimum_order_amount=Decimal("0"),
            delivery_fee=Decimal("30000"),
        )


def test_menu_item_create_validation() -> None:
    """Menu item schemas require a positive price and valid status."""
    request = MenuItemCreate(
        name="Pho",
        price=Decimal("50000"),
        category_id=uuid.uuid4(),
        status=MenuItemStatus.AVAILABLE,
    )

    assert request.preparation_time_minutes == 15
    assert request.allergens == []

    with pytest.raises(ValidationError):
        MenuItemCreate(name="Pho", price=Decimal("0"), category_id=uuid.uuid4())


def test_order_schemas_validation() -> None:
    """Order schemas require at least one item and valid quantities."""
    request = OrderCreate(
        restaurant_id=uuid.uuid4(),
        items=[OrderItemCreate(menu_item_id=uuid.uuid4(), quantity=2)],
        delivery_address=_order_address(),  # type: ignore[arg-type]
    )

    assert len(request.items) == 1
    assert OrderStatusUpdate(status=OrderStatus.CONFIRMED).status == OrderStatus.CONFIRMED

    with pytest.raises(ValidationError):
        OrderCreate(restaurant_id=uuid.uuid4(), items=[], delivery_address=_order_address())  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        OrderItemCreate(menu_item_id=uuid.uuid4(), quantity=101)


def test_promotion_and_review_validation() -> None:
    """Promotion and review schemas enforce numeric ranges."""
    promotion = PromotionCreate(
        code="WELCOME",
        title="Welcome discount",
        discount_type=DiscountType.FIXED_AMOUNT,
        discount_value=Decimal("10000"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )

    assert promotion.status == PromotionStatus.ACTIVE
    assert ReviewCreate(rating=5).images == []

    with pytest.raises(ValidationError):
        PromotionCreate(
            code="WELCOME",
            title="Welcome discount",
            discount_type=DiscountType.FIXED_AMOUNT,
            discount_value=Decimal("-1"),
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
        )
    with pytest.raises(ValidationError):
        ReviewCreate(rating=6)


def test_delivery_schemas_validation() -> None:
    """Delivery schemas accept provider and status enums."""
    assert DeliveryDispatchRequest(provider=DeliveryProvider.AHAMOVE).provider == DeliveryProvider.AHAMOVE
    assert DeliveryTrackingUpdate(status=DeliveryStatus.IN_TRANSIT).status == DeliveryStatus.IN_TRANSIT

    with pytest.raises(ValidationError):
        DeliveryDispatchRequest(provider="UNKNOWN")  # type: ignore[arg-type]
