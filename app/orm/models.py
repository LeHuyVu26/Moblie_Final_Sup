"""SQLAlchemy ORM models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import (
    DeliveryProvider,
    DeliveryStatus,
    MenuItemStatus,
    OrderStatus,
    PaymentStatus,
    PromotionType,
    UserRole,
)
from app.orm.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass


class User(Base, TimestampMixin):
    """User ORM model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    restaurants: Mapped[list[Restaurant]] = relationship(
        "Restaurant", back_populates="owner", cascade="all, delete-orphan"
    )
    orders: Mapped[list[Order]] = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    reviews: Mapped[list[Review]] = relationship("Review", back_populates="customer", cascade="all, delete-orphan")


class Restaurant(Base, TimestampMixin):
    """Restaurant ORM model."""

    __tablename__ = "restaurants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    street: Mapped[str] = mapped_column(String(200), nullable=False)
    ward: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    opening_time: Mapped[str] = mapped_column(String(5), nullable=False)
    closing_time: Mapped[str] = mapped_column(String(5), nullable=False)
    min_order_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    delivery_radius_km: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=5.0)
    rating: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False, default=0.0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    owner: Mapped[User] = relationship("User", back_populates="restaurants")
    categories: Mapped[list[Category]] = relationship(
        "Category", back_populates="restaurant", cascade="all, delete-orphan"
    )
    menu_items: Mapped[list[MenuItem]] = relationship(
        "MenuItem", back_populates="restaurant", cascade="all, delete-orphan"
    )
    promotions: Mapped[list[Promotion]] = relationship(
        "Promotion", back_populates="restaurant", cascade="all, delete-orphan"
    )
    orders: Mapped[list[Order]] = relationship("Order", back_populates="restaurant", cascade="all, delete-orphan")
    reviews: Mapped[list[Review]] = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")


class Category(Base, TimestampMixin):
    """Category ORM model."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="categories")
    menu_items: Mapped[list[MenuItem]] = relationship(
        "MenuItem", back_populates="category", cascade="all, delete-orphan"
    )


class MenuItem(Base, TimestampMixin):
    """Menu item ORM model."""

    __tablename__ = "menu_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[MenuItemStatus] = mapped_column(
        Enum(MenuItemStatus), default=MenuItemStatus.AVAILABLE, nullable=False
    )
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_vegan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_spicy: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preparation_time_minutes: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    allergens: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="menu_items")
    category: Mapped[Category] = relationship("Category", back_populates="menu_items")
    order_items: Mapped[list[OrderItem]] = relationship(
        "OrderItem", back_populates="menu_item", cascade="all, delete-orphan"
    )


class Promotion(Base, TimestampMixin):
    """Promotion ORM model."""

    __tablename__ = "promotions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[PromotionType] = mapped_column(Enum(PromotionType), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_order_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    max_discount_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    user_usage_limit: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    applicable_menu_item_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    applicable_category_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="promotions")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="promotion")


class Order(Base, TimestampMixin):
    """Order ORM model."""

    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    promotion_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("promotions.id"), nullable=True)
    promotion_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    street: Mapped[str] = mapped_column(String(200), nullable=False)
    ward: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    customer_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    restaurant_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_preparation_time_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    customer: Mapped[User] = relationship("User", back_populates="orders")
    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="orders")
    promotion: Mapped[Promotion | None] = relationship("Promotion", back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment: Mapped[Payment | None] = relationship(
        "Payment", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )
    delivery: Mapped[Delivery | None] = relationship(
        "Delivery", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )


class OrderItem(Base, TimestampMixin):
    """Order item ORM model."""

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    menu_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("menu_items.id"), nullable=False)
    menu_item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    menu_item_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")
    menu_item: Mapped[MenuItem] = relationship("MenuItem", back_populates="order_items")


class Payment(Base, TimestampMixin):
    """Payment ORM model."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False, unique=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="MOCK")
    provider_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped[Order] = relationship("Order", back_populates="payment")


class Delivery(Base, TimestampMixin):
    """Delivery ORM model."""

    __tablename__ = "deliveries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False, unique=True)
    provider: Mapped[DeliveryProvider] = mapped_column(Enum(DeliveryProvider), nullable=False)
    provider_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus), default=DeliveryStatus.PENDING_DISPATCH, nullable=False
    )
    driver_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    driver_vehicle: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driver_license_plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    driver_current_latitude: Mapped[float | None] = mapped_column(nullable=True)
    driver_current_longitude: Mapped[float | None] = mapped_column(nullable=True)
    pickup_street: Mapped[str] = mapped_column(String(200), nullable=False)
    pickup_ward: Mapped[str] = mapped_column(String(100), nullable=False)
    pickup_district: Mapped[str] = mapped_column(String(100), nullable=False)
    pickup_city: Mapped[str] = mapped_column(String(100), nullable=False)
    pickup_latitude: Mapped[float | None] = mapped_column(nullable=True)
    pickup_longitude: Mapped[float | None] = mapped_column(nullable=True)
    dropoff_street: Mapped[str] = mapped_column(String(200), nullable=False)
    dropoff_ward: Mapped[str] = mapped_column(String(100), nullable=False)
    dropoff_district: Mapped[str] = mapped_column(String(100), nullable=False)
    dropoff_city: Mapped[str] = mapped_column(String(100), nullable=False)
    dropoff_latitude: Mapped[float | None] = mapped_column(nullable=True)
    dropoff_longitude: Mapped[float | None] = mapped_column(nullable=True)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    picked_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    tracking_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    order: Mapped[Order] = relationship("Order", back_populates="delivery")


class Review(Base, TimestampMixin):
    """Review ORM model."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    restaurant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("restaurants.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False, unique=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    images: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    customer: Mapped[User] = relationship("User", back_populates="reviews")
    restaurant: Mapped[Restaurant] = relationship("Restaurant", back_populates="reviews")
    order: Mapped[Order] = relationship("Order")
