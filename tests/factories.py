"""Domain/ORM factories for tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
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
    DeliveryProvider,
    DeliveryStatus,
    MenuItemStatus,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    PromotionType,
    UserRole,
)
from app.domain.value_objects import Address, Coordinates, Money, PhoneNumber
from app.repositories.category import CategoryRepository
from app.repositories.delivery import DeliveryRepository
from app.repositories.menu_item import MenuItemRepository
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository
from app.repositories.promotion import PromotionRepository
from app.repositories.restaurant import RestaurantRepository
from app.repositories.review import ReviewRepository
from app.repositories.user import UserRepository

DEFAULT_PASSWORD = "Password123"


def _phone() -> str:
    return f"09{uuid.uuid4().int % 100_000_000:08d}"


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}@example.com"


def address(
    *,
    street: str = "123 Main Street",
    ward: str = "Ward 1",
    district: str = "District 1",
    city: str = "Ho Chi Minh City",
    latitude: float | None = 10.0,
    longitude: float | None = 106.0,
) -> Address:
    return Address(
        street=street,
        ward=ward,
        district=district,
        city=city,
        latitude=latitude,
        longitude=longitude,
    )


async def create_user(
    session: AsyncSession,
    *,
    email: str | None = None,
    phone: str | None = None,
    password: str = DEFAULT_PASSWORD,
    full_name: str = "Test User",
    role: UserRole = UserRole.CUSTOMER,
    is_active: bool = True,
) -> User:
    user = User(
        email=email or _email("user"),
        phone=PhoneNumber(number=PhoneNumber.normalize(phone or _phone())),
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    return await UserRepository(session).add(user)


async def create_restaurant(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    name: str = "Test Restaurant",
    is_active: bool = True,
    delivery_fee: Decimal = Decimal("30000"),
    min_order_amount: Decimal = Decimal("0"),
    latitude: float | None = 10.0,
    longitude: float | None = 106.0,
) -> Restaurant:
    if owner_id is None:
        owner = await create_user(session, role=UserRole.OWNER, full_name="Restaurant Owner")
        owner_id = owner.id
    restaurant = Restaurant(
        owner_id=owner_id,
        name=name,
        description="A test restaurant",
        address=address(latitude=latitude, longitude=longitude),
        phone=PhoneNumber(number=PhoneNumber.normalize(_phone())),
        email=_email("restaurant"),
        opening_time="08:00",
        closing_time="22:00",
        min_order_amount=Money(amount=min_order_amount),
        delivery_fee=Money(amount=delivery_fee),
        delivery_radius_km=Decimal("5.0"),
        is_active=is_active,
    )
    return await RestaurantRepository(session).add(restaurant)


async def create_category(
    session: AsyncSession,
    *,
    restaurant_id: uuid.UUID | None = None,
    name: str = "Main",
    display_order: int = 0,
) -> Category:
    if restaurant_id is None:
        restaurant = await create_restaurant(session)
        restaurant_id = restaurant.id
    category = Category(
        restaurant_id=restaurant_id,
        name=name,
        description="Test category",
        display_order=display_order,
    )
    return await CategoryRepository(session).add(category)


async def create_menu_item(
    session: AsyncSession,
    *,
    restaurant_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    name: str = "Pho",
    price: Decimal = Decimal("50000"),
    original_price: Decimal | None = None,
    status: MenuItemStatus = MenuItemStatus.AVAILABLE,
    allergens: list[str] | None = None,
    display_order: int = 0,
) -> MenuItem:
    if category_id is None:
        category = await create_category(session, restaurant_id=restaurant_id)
        category_id = category.id
        restaurant_id = category.restaurant_id
    if restaurant_id is None:
        found_category = await CategoryRepository(session).get(category_id)
        assert found_category is not None
        restaurant_id = found_category.restaurant_id
    item = MenuItem(
        restaurant_id=restaurant_id,
        category_id=category_id,
        name=name,
        description="A test menu item",
        price=Money(amount=price),
        original_price=Money(amount=original_price) if original_price is not None else None,
        status=status,
        allergens=allergens or [],
        display_order=display_order,
    )
    return await MenuItemRepository(session).add(item)


async def create_promotion(
    session: AsyncSession,
    *,
    restaurant_id: uuid.UUID | None = None,
    name: str = "WELCOME",
    type: PromotionType = PromotionType.PERCENTAGE,
    value: Decimal = Decimal("10"),
    min_order_amount: Decimal | None = None,
    max_discount_amount: Decimal | None = None,
    usage_limit: int | None = None,
    usage_count: int = 0,
    is_active: bool = True,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    applicable_menu_item_ids: list[uuid.UUID] | None = None,
    applicable_category_ids: list[uuid.UUID] | None = None,
) -> Promotion:
    if restaurant_id is None:
        restaurant = await create_restaurant(session)
        restaurant_id = restaurant.id
    now = datetime.utcnow()
    promotion = Promotion(
        restaurant_id=restaurant_id,
        name=name,
        description="Test promotion",
        type=type,
        value=value,
        min_order_amount=Money(amount=min_order_amount) if min_order_amount is not None else None,
        max_discount_amount=Money(amount=max_discount_amount) if max_discount_amount is not None else None,
        usage_limit=usage_limit,
        usage_count=usage_count,
        is_active=is_active,
        start_at=start_at or now - timedelta(days=1),
        end_at=end_at or now + timedelta(days=1),
        applicable_menu_item_ids=applicable_menu_item_ids or [],
        applicable_category_ids=applicable_category_ids or [],
    )
    return await PromotionRepository(session).add(promotion)


async def create_order(
    session: AsyncSession,
    *,
    customer_id: uuid.UUID | None = None,
    restaurant_id: uuid.UUID | None = None,
    items: list[tuple[MenuItem, int, str | None]] | None = None,
    status: OrderStatus = OrderStatus.PENDING,
    promotion_id: uuid.UUID | None = None,
    promotion_code: str | None = None,
    discount: Decimal = Decimal("0"),
    customer_note: str | None = None,
    delivery_address: Address | None = None,
) -> Order:
    if customer_id is None:
        customer = await create_user(session, full_name="Order Customer")
        customer_id = customer.id
    if restaurant_id is None:
        restaurant = await create_restaurant(session)
        restaurant_id = restaurant.id
    found_restaurant = await RestaurantRepository(session).get(restaurant_id)
    assert found_restaurant is not None
    restaurant = found_restaurant

    if items is None:
        menu_item = await create_menu_item(session, restaurant_id=restaurant_id)
        items = [(menu_item, 1, None)]

    order_items: list[OrderItem] = []
    subtotal = Decimal("0")
    for menu_item, quantity, note in items:
        item = OrderItem.create(
            order_id=uuid.uuid4(),
            menu_item_id=menu_item.id,
            menu_item_name=menu_item.name,
            menu_item_price=menu_item.price,
            quantity=quantity,
            note=note,
        )
        order_items.append(item)
        subtotal += item.subtotal.amount

    delivery_fee = restaurant.delivery_fee.amount
    order = Order(
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        status=status,
        items=order_items,
        subtotal=Money(amount=subtotal),
        delivery_fee=Money(amount=delivery_fee),
        discount_amount=Money(amount=discount),
        total_amount=Money(amount=subtotal + delivery_fee - discount),
        promotion_id=promotion_id,
        promotion_code=promotion_code,
        delivery_address=delivery_address or address(),
        delivery_coordinates=Coordinates(latitude=10.0, longitude=106.0),
        customer_note=customer_note,
    )
    for item in order.items:
        item.order_id = order.id

    # OrderRepository.add() calls _to_domain() after refresh, which lazily loads
    # model.items and fails under async SQLAlchemy. Insert the ORM model directly,
    # then read it back through OrderRepository.get(), which uses selectinload.
    repo = OrderRepository(session)
    model = repo._to_model(order)
    session.add(model)
    await session.flush()
    await session.refresh(model)
    fetched = await repo.get(order.id)
    assert fetched is not None
    return fetched


async def create_payment(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    status: PaymentStatus = PaymentStatus.PROCESSING,
    method: PaymentMethod = PaymentMethod.MOMO,
    transaction_id: str | None = "MOCK-TXN-123",
    provider_response: dict[str, object] | None = None,
) -> Payment:
    order = await OrderRepository(session).get(order_id)
    assert order is not None
    payment = Payment(
        order_id=order_id,
        amount=order.total_amount,
        status=status,
        provider=method,
        provider_transaction_id=transaction_id,
        provider_response=provider_response or {"provider": "MOCK"},
        paid_at=datetime.utcnow() if status == PaymentStatus.COMPLETED else None,
    )
    return await PaymentRepository(session).add(payment)


async def create_delivery(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    status: DeliveryStatus = DeliveryStatus.PENDING_DISPATCH,
    provider: DeliveryProvider = DeliveryProvider.AHAMOVE,
    driver_phone: str | None = None,
    tracking_url: str | None = None,
) -> Delivery:
    order = await OrderRepository(session).get(order_id)
    assert order is not None
    delivery = Delivery(
        order_id=order_id,
        provider=provider,
        status=status,
        pickup_address=address(street="Restaurant Street"),
        dropoff_address=order.delivery_address,
        dropoff_coordinates=order.delivery_coordinates,
        fee=order.delivery_fee,
        driver_phone=PhoneNumber(number=PhoneNumber.normalize(driver_phone)) if driver_phone else None,
        tracking_url=tracking_url,
        assigned_at=datetime.utcnow() if status != DeliveryStatus.PENDING_DISPATCH else None,
    )
    return await DeliveryRepository(session).add(delivery)


async def create_review(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    customer_id: uuid.UUID,
    restaurant_id: uuid.UUID,
    rating: int = 5,
    comment: str = "Great food",
    images: list[str] | None = None,
) -> Review:
    review = Review(
        order_id=order_id,
        customer_id=customer_id,
        restaurant_id=restaurant_id,
        rating=rating,
        comment=comment,
        images=images or [],
    )
    return await ReviewRepository(session).add(review)
