"""Menu management endpoint tests."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from tests.factories import create_category, create_menu_item, create_restaurant
from tests.helpers import assert_error, assert_page, assert_requires_auth


def _category_payload() -> dict[str, object]:
    return {"name": "Mains", "description": "Main dishes", "display_order": 1}


def _item_payload(category_id: uuid.UUID) -> dict[str, object]:
    return {
        "category_id": str(category_id),
        "name": "Pho",
        "description": "Noodle soup",
        "price": "50000",
        "discounted_price": "45000",
        "status": "AVAILABLE",
        "preparation_time_minutes": 15,
        "allergens": ["peanut"],
    }


def _promotion_payload() -> dict[str, object]:
    today = date.today()
    return {
        "code": "SAVE10",
        "title": "Save 10 percent",
        "description": "Promotion for tests",
        "discount_type": "PERCENTAGE",
        "discount_value": "10",
        "minimum_order_amount": "0",
        "start_date": str(today - timedelta(days=1)),
        "end_date": str(today + timedelta(days=1)),
        "status": "ACTIVE",
        "applicable_item_ids": [],
        "applicable_category_ids": [],
    }


async def test_category_endpoints(client_factory, session, owner_user, customer_user) -> None:
    """Category CRUD endpoints enforce ownership."""
    restaurant = await create_restaurant(session, owner_id=owner_user.id)

    async with client_factory(owner_user) as client:
        created = await client.post(f"/v1/menu/{restaurant.id}/categories", json=_category_payload())
        assert created.status_code == 200
        category_id = created.json()["id"]
        assert created.json()["name"] == "Mains"

        listed = await client.get(f"/v1/menu/{restaurant.id}/categories")
        assert listed.status_code == 200
        assert [item["id"] for item in assert_page(listed.json())] == [category_id]

        updated = await client.patch(f"/v1/menu/categories/{category_id}", json={"name": "Updated Mains"})
        assert updated.status_code == 200
        assert updated.json()["name"] == "Updated Mains"

    async with client_factory(customer_user) as client:
        forbidden = await client.post(f"/v1/menu/{restaurant.id}/categories", json=_category_payload())
        assert_error(forbidden, 403, "Not allowed")

    async with client_factory(owner_user) as client:
        deleted = await client.delete(f"/v1/menu/categories/{category_id}")
        assert deleted.status_code == 200
        assert deleted.json() == {"message": "Category deleted"}
        missing = await client.patch(f"/v1/menu/categories/{category_id}", json={"name": "Gone"})
        assert_error(missing, 404, "Category not found")

    async with client_factory(None) as client:
        await assert_requires_auth(client, "POST", f"/v1/menu/{restaurant.id}/categories", json=_category_payload())


async def test_menu_item_endpoints(client_factory, session, owner_user) -> None:
    """Menu item CRUD endpoints work for owners."""
    restaurant = await create_restaurant(session, owner_id=owner_user.id)
    category = await create_category(session, restaurant_id=restaurant.id)

    async with client_factory(owner_user) as client:
        created = await client.post(f"/v1/menu/{restaurant.id}/items", json=_item_payload(category.id))
        assert created.status_code == 200
        item_id = created.json()["id"]
        assert Decimal(created.json()["price"]) == Decimal("50000")
        assert Decimal(created.json()["discounted_price"]) == Decimal("45000")
        assert created.json()["allergens"] == ["peanut"]

        listed = await client.get(f"/v1/menu/{restaurant.id}/items")
        assert listed.status_code == 200
        assert [item["id"] for item in assert_page(listed.json())] == [item_id]

        updated = await client.patch(f"/v1/menu/items/{item_id}", json={"price": "60000", "name": "Special Pho"})
        assert updated.status_code == 200
        assert Decimal(updated.json()["price"]) == Decimal("60000")
        assert updated.json()["name"] == "Special Pho"

        deleted = await client.delete(f"/v1/menu/items/{item_id}")
        assert deleted.status_code == 200
        assert deleted.json() == {"message": "Menu item deleted"}
        missing = await client.get(f"/v1/menu/{restaurant.id}/items")
        assert missing.status_code == 200
        assert assert_page(missing.json()) == []


async def test_promotion_endpoints(client_factory, session, owner_user) -> None:
    """Promotion CRUD endpoints work for owners."""
    restaurant = await create_restaurant(session, owner_id=owner_user.id)

    async with client_factory(owner_user) as client:
        created = await client.post(f"/v1/menu/{restaurant.id}/promotions", json=_promotion_payload())
        assert created.status_code == 200
        promotion_id = created.json()["id"]
        assert created.json()["code"] == "SAVE10"
        assert created.json()["title"] == "SAVE10"
        assert created.json()["discount_type"] == "PERCENTAGE"

        listed = await client.get(f"/v1/menu/{restaurant.id}/promotions")
        assert listed.status_code == 200
        assert [item["id"] for item in assert_page(listed.json())] == [promotion_id]

        updated = await client.patch(f"/v1/menu/promotions/{promotion_id}", json={"code": "SAVE20"})
        assert updated.status_code == 200
        assert updated.json()["code"] == "SAVE20"

        deleted = await client.delete(f"/v1/menu/promotions/{promotion_id}")
        assert deleted.status_code == 200
        assert deleted.json() == {"message": "Promotion deleted"}
        missing = await client.patch(f"/v1/menu/promotions/{promotion_id}", json={"code": "GONE"})
        assert_error(missing, 404, "Promotion not found")


async def test_menu_item_not_found_and_unauthenticated(client_factory, session, owner_user) -> None:
    """Menu item update validates existence and authentication."""
    restaurant = await create_restaurant(session, owner_id=owner_user.id)
    item = await create_menu_item(session, restaurant_id=restaurant.id)

    async with client_factory(owner_user) as client:
        missing = await client.patch(f"/v1/menu/items/{uuid.uuid4()}", json={"name": "Nobody"})
        assert_error(missing, 404, "Menu item not found")

    async with client_factory(None) as client:
        await assert_requires_auth(client, "PATCH", f"/v1/menu/items/{item.id}", json={"name": "No auth"})
