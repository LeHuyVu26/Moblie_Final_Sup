"""Restaurant, category, menu item, and promotion repository tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import MenuItemStatus, PromotionType, UserRole
from app.repositories.category import CategoryRepository
from app.repositories.menu_item import MenuItemRepository
from app.repositories.promotion import PromotionRepository
from app.repositories.restaurant import RestaurantRepository
from tests.factories import (
    create_category,
    create_menu_item,
    create_promotion,
    create_restaurant,
    create_user,
)


async def test_restaurant_repository_crud_and_filters(session: AsyncSession) -> None:
    repo = RestaurantRepository(session)
    owner = await create_user(session, role=UserRole.OWNER)
    restaurant = await create_restaurant(session, owner_id=owner.id, name="Active Place")
    inactive = await create_restaurant(session, owner_id=owner.id, name="Inactive Place", is_active=False)

    fetched = await repo.get(restaurant.id)
    assert fetched is not None and fetched.name == "Active Place"
    assert fetched.address.street == restaurant.address.street
    assert fetched.min_order_amount.amount == restaurant.min_order_amount.amount

    by_owner = await repo.get_by_owner(owner.id)
    assert {item.id for item in by_owner} == {restaurant.id, inactive.id}
    active = await repo.list_active()
    assert [item.id for item in active] == [restaurant.id]

    restaurant.name = "Renamed Place"
    updated = await repo.update(restaurant)
    assert updated.name == "Renamed Place"

    assert await repo.remove(inactive.id) is True
    assert await repo.get(inactive.id) is None


async def test_category_repository_ordered_by_display_order(session: AsyncSession) -> None:
    repo = CategoryRepository(session)
    restaurant = await create_restaurant(session)
    second = await create_category(session, restaurant_id=restaurant.id, name="Second", display_order=2)
    first = await create_category(session, restaurant_id=restaurant.id, name="First", display_order=1)

    categories = await repo.get_by_restaurant(restaurant.id)

    assert [item.id for item in categories] == [first.id, second.id]
    assert (await repo.get(first.id)) is not None
    assert await repo.remove(first.id) is True
    assert await repo.get(first.id) is None


async def test_menu_item_repository_filters_and_allergens(session: AsyncSession) -> None:
    repo = MenuItemRepository(session)
    restaurant = await create_restaurant(session)
    category = await create_category(session, restaurant_id=restaurant.id)
    available = await create_menu_item(
        session,
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Available",
        allergens=["peanut", "sesame"],
        display_order=1,
    )
    hidden = await create_menu_item(
        session,
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Hidden",
        status=MenuItemStatus.HIDDEN,
        display_order=2,
    )

    fetched = await repo.get(available.id)
    assert fetched is not None
    assert fetched.allergens == ["peanut", "sesame"]
    assert fetched.price.amount == Decimal("50000")

    by_restaurant = await repo.get_by_restaurant(restaurant.id)
    by_category = await repo.get_by_category(category.id)
    available_items = await repo.get_available_by_restaurant(restaurant.id)
    assert [item.id for item in by_restaurant] == [available.id, hidden.id]
    assert [item.id for item in by_category] == [available.id, hidden.id]
    assert [item.id for item in available_items] == [available.id]

    available.name = "Updated"
    available.allergens = ["gluten"]
    updated = await repo.update(available)
    assert updated.name == "Updated"
    assert updated.allergens == ["gluten"]


async def test_promotion_repository_filters_and_uuid_csv(session: AsyncSession) -> None:
    repo = PromotionRepository(session)
    restaurant = await create_restaurant(session)
    item_id = uuid.uuid4()
    category_id = uuid.uuid4()
    now = datetime.utcnow()
    active = await create_promotion(
        session,
        restaurant_id=restaurant.id,
        name="ACTIVE",
        applicable_menu_item_ids=[item_id],
        applicable_category_ids=[category_id],
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=1),
    )
    inactive = await create_promotion(
        session,
        restaurant_id=restaurant.id,
        name="INACTIVE",
        is_active=False,
    )

    fetched = await repo.get(active.id)
    assert fetched is not None
    assert fetched.applicable_menu_item_ids == [item_id]
    assert fetched.applicable_category_ids == [category_id]
    assert fetched.type == PromotionType.PERCENTAGE

    by_restaurant = await repo.get_by_restaurant(restaurant.id)
    assert {item.id for item in by_restaurant} == {active.id, inactive.id}

    active_now = await repo.get_active_by_restaurant(restaurant.id, at=now)
    assert [item.id for item in active_now] == [active.id]

    expired = await repo.get_active_by_restaurant(restaurant.id, at=now + timedelta(days=2))
    assert expired == []

    active.usage_count = 1
    updated = await repo.update(active)
    assert updated.usage_count == 1
