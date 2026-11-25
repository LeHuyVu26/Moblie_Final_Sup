"""Explicit mappers from domain entities to API response schemas."""

from __future__ import annotations

from datetime import time
from decimal import Decimal
from typing import TypeVar

from app.api.schemas.categories import CategoryResponse
from app.api.schemas.common import Page
from app.api.schemas.deliveries import DeliveryAddress, DeliveryResponse
from app.api.schemas.menu_items import MenuItemResponse
from app.api.schemas.orders import (
    OrderAddress,
    OrderItemResponse,
    OrderResponse,
    OrderSummaryResponse,
)
from app.api.schemas.payments import PaymentResponse
from app.api.schemas.promotions import PromotionResponse
from app.api.schemas.restaurants import RestaurantResponse, RestaurantSummaryResponse
from app.api.schemas.reviews import ReviewResponse
from app.api.schemas.users import UserProfileResponse, UserResponse
from app.domain.entities import (
    Category,
    Delivery,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    Promotion,
    Restaurant,
    Review,
    User,
)
from app.domain.enums import (
    DiscountType,
    PaymentMethod,
    PaymentStatus,
    PromotionStatus,
    RestaurantStatus,
)
from app.domain.value_objects import Address, Money, PhoneNumber

T = TypeVar("T")


def _money(value: Money) -> Decimal:
    """Convert Money value object to Decimal."""
    return value.amount


def _money_optional(value: Money | None) -> Decimal | None:
    """Convert optional Money value object to Decimal."""
    return value.amount if value is not None else None


def _decimal_optional(value: float | None) -> Decimal | None:
    """Convert optional float coordinate to Decimal."""
    return Decimal(str(value)) if value is not None else None


def _phone(value: PhoneNumber) -> str:
    """Convert PhoneNumber value object to string."""
    return value.number


def _phone_optional(value: PhoneNumber | None) -> str | None:
    """Convert optional PhoneNumber value object to string."""
    return value.number if value is not None else None


def _address(value: Address) -> OrderAddress:
    """Convert domain Address to API OrderAddress."""
    return OrderAddress(
        street=value.street,
        ward=value.ward,
        district=value.district,
        city=value.city,
        latitude=_decimal_optional(value.latitude),
        longitude=_decimal_optional(value.longitude),
        contact_name=None,
        contact_phone=None,
    )


def _delivery_address(value: Address) -> DeliveryAddress:
    """Convert domain Address to API DeliveryAddress."""
    return DeliveryAddress(
        street=value.street,
        ward=value.ward,
        district=value.district,
        city=value.city,
        latitude=_decimal_optional(value.latitude),
        longitude=_decimal_optional(value.longitude),
    )


def map_user(user: User) -> UserResponse:
    """Map User domain entity to API response."""
    return UserResponse(
        id=user.id,
        email=user.email,
        phone=_phone(user.phone),
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def map_user_profile(user: User) -> UserProfileResponse:
    """Map User domain entity to profile response."""
    return UserProfileResponse(
        id=user.id,
        email=user.email,
        phone=_phone(user.phone),
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def map_restaurant(restaurant: Restaurant) -> RestaurantResponse:
    """Map Restaurant domain entity to API response."""
    return RestaurantResponse(
        id=restaurant.id,
        owner_id=restaurant.owner_id,
        name=restaurant.name,
        description=restaurant.description,
        street=restaurant.address.street,
        ward=restaurant.address.ward,
        district=restaurant.address.district,
        city=restaurant.address.city,
        latitude=_decimal_optional(restaurant.address.latitude),
        longitude=_decimal_optional(restaurant.address.longitude),
        phone=_phone(restaurant.phone),
        email=restaurant.email,
        cuisine_type=None,
        opening_time=time.fromisoformat(restaurant.opening_time),
        closing_time=time.fromisoformat(restaurant.closing_time),
        delivery_radius_km=restaurant.delivery_radius_km,
        minimum_order_amount=_money(restaurant.min_order_amount),
        delivery_fee=_money(restaurant.delivery_fee),
        status=RestaurantStatus.ACTIVE if restaurant.is_active else RestaurantStatus.SUSPENDED,
        avatar_url=restaurant.logo_url,
        cover_url=restaurant.cover_image_url,
        created_at=restaurant.created_at,
        updated_at=restaurant.updated_at,
    )


def map_restaurant_summary(restaurant: Restaurant) -> RestaurantSummaryResponse:
    """Map Restaurant domain entity to summary response."""
    return RestaurantSummaryResponse(
        id=restaurant.id,
        name=restaurant.name,
        cuisine_type=None,
        status=RestaurantStatus.ACTIVE if restaurant.is_active else RestaurantStatus.SUSPENDED,
        minimum_order_amount=_money(restaurant.min_order_amount),
        delivery_fee=_money(restaurant.delivery_fee),
        avatar_url=restaurant.logo_url,
        cover_url=restaurant.cover_image_url,
    )


def map_category(category: Category) -> CategoryResponse:
    """Map Category domain entity to API response."""
    return CategoryResponse(
        id=category.id,
        restaurant_id=category.restaurant_id,
        name=category.name,
        description=category.description,
        display_order=category.display_order,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


def map_menu_item(item: MenuItem) -> MenuItemResponse:
    """Map MenuItem domain entity to API response."""
    return MenuItemResponse(
        id=item.id,
        restaurant_id=item.restaurant_id,
        category_id=item.category_id,
        name=item.name,
        description=item.description,
        price=_money(item.price),
        discounted_price=_money_optional(item.original_price),
        image_url=item.image_url,
        status=item.status,
        is_featured=False,
        preparation_time_minutes=item.preparation_time_minutes,
        allergens=item.allergens,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def map_promotion(promotion: Promotion) -> PromotionResponse:
    """Map Promotion domain entity to API response."""
    return PromotionResponse(
        id=promotion.id,
        restaurant_id=promotion.restaurant_id,
        code=promotion.name,
        title=promotion.name,
        description=promotion.description,
        discount_type=(
            DiscountType(promotion.type)
            if promotion.type in DiscountType._value2member_map_
            else DiscountType.FIXED_AMOUNT
        ),
        discount_value=promotion.value,
        minimum_order_amount=_money(promotion.min_order_amount) if promotion.min_order_amount else Decimal("0"),
        maximum_discount_amount=_money_optional(promotion.max_discount_amount),
        start_date=promotion.start_at.date(),
        end_date=promotion.end_at.date(),
        usage_limit=promotion.usage_limit,
        status=PromotionStatus.ACTIVE if promotion.is_active else PromotionStatus.INACTIVE,
        applicable_item_ids=promotion.applicable_menu_item_ids,
        applicable_category_ids=promotion.applicable_category_ids,
        created_at=promotion.created_at,
        updated_at=promotion.updated_at,
    )


def map_order_item(item: OrderItem) -> OrderItemResponse:
    """Map OrderItem domain entity to API response."""
    return OrderItemResponse(
        id=item.id,
        menu_item_id=item.menu_item_id,
        menu_item_name=item.menu_item_name,
        unit_price=_money(item.menu_item_price),
        quantity=item.quantity,
        subtotal=_money(item.subtotal),
        special_instructions=item.note,
    )


def map_order(
    order: Order, *, restaurant_name: str = "", payment_status: PaymentStatus = PaymentStatus.PENDING
) -> OrderResponse:
    """Map Order domain entity to API response."""
    return OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        restaurant_id=order.restaurant_id,
        restaurant_name=restaurant_name,
        status=order.status,
        payment_status=payment_status,
        items=[map_order_item(item) for item in order.items],
        subtotal=_money(order.subtotal),
        discount_amount=_money(order.discount_amount),
        delivery_fee=_money(order.delivery_fee),
        total_amount=_money(order.total_amount),
        delivery_address=_address(order.delivery_address),
        promotion_code=order.promotion_code,
        notes=order.customer_note,
        scheduled_for=None,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def map_order_summary(
    order: Order, *, restaurant_name: str = "", payment_status: PaymentStatus = PaymentStatus.PENDING
) -> OrderSummaryResponse:
    """Map Order domain entity to summary response."""
    return OrderSummaryResponse(
        id=order.id,
        restaurant_name=restaurant_name,
        status=order.status,
        payment_status=payment_status,
        total_amount=_money(order.total_amount),
        created_at=order.created_at,
    )


def map_payment(payment: Payment) -> PaymentResponse:
    """Map Payment domain entity to API response."""
    return PaymentResponse(
        id=payment.id,
        order_id=payment.order_id,
        method=PaymentMethod(payment.provider)
        if payment.provider in PaymentMethod._value2member_map_
        else PaymentMethod.CASH,
        amount=_money(payment.amount),
        status=payment.status,
        transaction_id=payment.provider_transaction_id,
        paid_at=payment.paid_at,
        provider_response=payment.provider_response,
        created_at=payment.created_at,
        updated_at=payment.updated_at,
    )


def map_delivery(delivery: Delivery) -> DeliveryResponse:
    """Map Delivery domain entity to API response."""
    return DeliveryResponse(
        id=delivery.id,
        order_id=delivery.order_id,
        status=delivery.status,
        provider=delivery.provider,
        provider_order_id=delivery.provider_order_id,
        driver_name=delivery.driver_name,
        driver_phone=_phone_optional(delivery.driver_phone),
        tracking_url=delivery.tracking_url,
        pickup_address=_delivery_address(delivery.pickup_address),
        dropoff_address=_delivery_address(delivery.dropoff_address),
        fee=_money(delivery.fee),
        estimated_pickup_at=None,
        estimated_dropoff_at=None,
        picked_up_at=delivery.picked_up_at,
        delivered_at=delivery.delivered_at,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
    )


def map_review(review: Review, *, customer_name: str = "") -> ReviewResponse:
    """Map Review domain entity to API response."""
    return ReviewResponse(
        id=review.id,
        order_id=review.order_id,
        restaurant_id=review.restaurant_id,
        customer_id=review.customer_id,
        customer_name=customer_name,
        rating=review.rating,
        comment=review.comment,
        images=review.images,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def map_page(items: list[T], total: int, page: int, size: int) -> Page[T]:
    """Build a paginated response."""
    return Page(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size else 0,
    )
