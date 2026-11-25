"""Restaurant endpoint tests."""

from __future__ import annotations

import uuid

from tests.factories import create_restaurant
from tests.helpers import assert_error, assert_page, assert_requires_auth


def _restaurant_payload() -> dict[str, object]:
    return {
        "name": "New Restaurant",
        "description": "A new place",
        "street": "123 Main Street",
        "ward": "Ward 1",
        "district": "District 1",
        "city": "Ho Chi Minh City",
        "latitude": "10.0",
        "longitude": "106.0",
        "phone": "0912345678",
        "email": "restaurant@example.com",
        "opening_time": "08:00",
        "closing_time": "22:00",
        "delivery_radius_km": "5.0",
        "minimum_order_amount": "0",
        "delivery_fee": "30000",
    }


async def test_list_and_get_restaurants(client_factory, session) -> None:
    """Public restaurant listing and detail endpoints work."""
    restaurant = await create_restaurant(session, name="Visible Restaurant")
    inactive = await create_restaurant(session, name="Hidden Restaurant", is_active=False)

    async with client_factory(None) as client:
        listed = await client.get("/v1/restaurant/")
        assert listed.status_code == 200
        items = assert_page(listed.json())
        assert [item["id"] for item in items] == [str(restaurant.id)]

        found = await client.get(f"/v1/restaurant/{restaurant.id}")
        assert found.status_code == 200
        assert found.json()["name"] == "Visible Restaurant"
        assert found.json()["status"] == "ACTIVE"

        missing = await client.get(f"/v1/restaurant/{uuid.uuid4()}")
        assert_error(missing, 404, "Restaurant not found")

    assert inactive.name == "Hidden Restaurant"


async def test_create_restaurant_owner_only(client_factory, owner_user, customer_user) -> None:
    """Only owners can create restaurants."""
    async with client_factory(owner_user) as client:
        response = await client.post("/v1/restaurant/", json=_restaurant_payload())
    assert response.status_code == 200
    assert response.json()["owner_id"] == str(owner_user.id)
    assert response.json()["name"] == "New Restaurant"

    async with client_factory(customer_user) as client:
        forbidden = await client.post("/v1/restaurant/", json=_restaurant_payload())
    assert_error(forbidden, 403, "Only owners can create restaurants")

    async with client_factory(None) as client:
        await assert_requires_auth(client, "POST", "/v1/restaurant/", json=_restaurant_payload())


async def test_update_and_delete_restaurant(client_factory, session, owner_user, customer_user) -> None:
    """Owners can update and delete their restaurants."""
    restaurant = await create_restaurant(session, owner_id=owner_user.id)

    async with client_factory(owner_user) as client:
        updated = await client.patch(f"/v1/restaurant/{restaurant.id}", json={"name": "Renamed Restaurant"})
        assert updated.status_code == 200
        assert updated.json()["name"] == "Renamed Restaurant"

    async with client_factory(customer_user) as client:
        forbidden = await client.patch(f"/v1/restaurant/{restaurant.id}", json={"name": "Not Allowed"})
        assert_error(forbidden, 403, "Not allowed")

    async with client_factory(owner_user) as client:
        deleted = await client.delete(f"/v1/restaurant/{restaurant.id}")
        assert deleted.status_code == 200
        assert deleted.json() == {"message": "Restaurant deleted"}
        missing = await client.delete(f"/v1/restaurant/{restaurant.id}")
        assert_error(missing, 404, "Restaurant not found")
