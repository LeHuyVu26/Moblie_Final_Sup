"""Tests for the shared repository base and ORM/domain mapping helpers."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User
from app.domain.enums import UserRole
from app.domain.value_objects import Coordinates, Money, PhoneNumber
from app.repositories.mappers import (
    address,
    coordinates,
    dumps_json,
    join_csv,
    join_csv_uuids,
    loads_json,
    money,
    money_required,
    phone,
    phone_optional,
    split_csv,
    split_csv_uuids,
)
from app.repositories.user import UserRepository
from tests.factories import create_user


async def test_base_repository_add_get_update_remove(session: AsyncSession) -> None:
    """BaseRepository CRUD works through a concrete repository."""
    repo = UserRepository(session)
    user = User(
        email="base@example.com",
        phone=PhoneNumber(number=PhoneNumber.normalize("0912345678")),
        full_name="Base User",
        password_hash="hashed",
        role=UserRole.CUSTOMER,
    )

    saved = await repo.add(user)
    assert saved.id == user.id
    assert saved.full_name == "Base User"

    fetched = await repo.get(user.id)
    assert fetched is not None
    assert fetched.email == "base@example.com"

    fetched.full_name = "Renamed User"
    updated = await repo.update(fetched)
    assert updated.full_name == "Renamed User"
    persisted = await repo.get(user.id)
    assert persisted is not None
    assert persisted.full_name == "Renamed User"

    assert await repo.remove(user.id) is True
    assert await repo.get(user.id) is None


async def test_base_repository_update_missing_raises(session: AsyncSession) -> None:
    """Updating an entity that is not persisted raises a ValueError."""
    repo = UserRepository(session)
    user = await create_user(session, email="ghost@example.com")

    await repo.remove(user.id)

    try:
        await repo.update(user)
    except ValueError as exc:
        assert str(exc) == f"Entity {user.id} not found"
    else:
        raise AssertionError("Expected ValueError for missing entity")


async def test_base_repository_remove_missing_returns_false(session: AsyncSession) -> None:
    """Removing an unknown id returns False instead of raising."""
    repo = UserRepository(session)

    assert await repo.remove(uuid.uuid4()) is False


async def test_base_repository_list_with_limit_and_offset(session: AsyncSession) -> None:
    """BaseRepository.list honours pagination."""
    repo = UserRepository(session)
    for index in range(3):
        await create_user(session, email=f"list-{index}@example.com")

    first_page = await repo.list(limit=2, offset=0)
    second_page = await repo.list(limit=2, offset=2)

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {user.id for user in first_page}.isdisjoint({user.id for user in second_page})


def test_money_helpers() -> None:
    """money/money_required build Money from valid decimal amounts."""
    assert money(None) is None
    assert money(Decimal("12.34")) == Money(amount=Decimal("12.34"))
    assert money_required(Decimal("7")) == Money(amount=Decimal("7.00"))


def test_phone_helpers() -> None:
    """phone helpers normalize Vietnamese numbers to +84 format."""
    assert phone("0912345678").number == "+84912345678"
    assert phone_optional(None) is None
    optional_phone = phone_optional("+84912345678")
    assert optional_phone is not None
    assert optional_phone.number == "+84912345678"


def test_address_and_coordinates_helpers() -> None:
    """address builds a value object; coordinates requires both axes."""
    built = address(
        street="1 Main",
        ward="Ward 1",
        district="District 1",
        city="HCMC",
        latitude=10.0,
        longitude=106.0,
    )
    assert built.full_address() == "1 Main, Ward 1, District 1, HCMC"
    assert built.latitude == 10.0

    assert coordinates(10.0, 106.0) == Coordinates(latitude=10.0, longitude=106.0)
    assert coordinates(None, 106.0) is None
    assert coordinates(10.0, None) is None


def test_csv_helpers() -> None:
    """CSV helpers round-trip lists and treat empty input as empty/None."""
    first = uuid.uuid4()
    second = uuid.uuid4()

    assert join_csv_uuids([]) is None
    assert join_csv_uuids([first, second]) == f"{first},{second}"
    assert split_csv_uuids(None) == []
    assert split_csv_uuids("") == []
    assert split_csv_uuids(f"{first}, ,{second}") == [first, second]

    assert join_csv([]) is None
    assert join_csv(["a", "b"]) == "a,b"
    assert split_csv(None) == []
    assert split_csv("a,, b") == ["a", " b"]


def test_json_helpers() -> None:
    """JSON helpers round-trip dicts and fall back to {} for invalid payloads."""
    payload = {"provider": "MOCK", "attempts": 1}

    assert dumps_json(None) is None
    assert dumps_json({}) is None
    encoded = dumps_json(payload)
    assert encoded is not None
    assert loads_json(encoded) == payload
    assert loads_json(None) == {}
    assert loads_json("") == {}
    assert loads_json("[1, 2]") == {}
