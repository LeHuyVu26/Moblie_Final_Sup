"""User repository tests."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import UserRole
from app.repositories.user import UserRepository
from tests.factories import create_user


async def test_user_repository_round_trip(session: AsyncSession) -> None:
    repo = UserRepository(session)
    user = await create_user(session, email="roundtrip@example.com", full_name="Round Trip")

    fetched = await repo.get(user.id)

    assert fetched is not None
    assert fetched.id == user.id
    assert fetched.email == "roundtrip@example.com"
    assert fetched.full_name == "Round Trip"
    assert fetched.phone.number == user.phone.number
    assert fetched.role == UserRole.CUSTOMER


async def test_user_repository_get_by_email_and_phone(session: AsyncSession) -> None:
    repo = UserRepository(session)
    user = await create_user(session, email="lookup@example.com", phone="0911111111")

    by_email = await repo.get_by_email("lookup@example.com")
    by_phone = await repo.get_by_phone(user.phone.number)

    assert by_email is not None and by_email.id == user.id
    assert by_phone is not None and by_phone.id == user.id
    assert await repo.get_by_email("missing@example.com") is None
    assert await repo.get_by_phone("0999999999") is None


async def test_user_repository_get_by_role_and_pagination(session: AsyncSession) -> None:
    repo = UserRepository(session)
    await create_user(session, role=UserRole.STAFF)
    await create_user(session, role=UserRole.STAFF)
    await create_user(session, role=UserRole.CUSTOMER)

    staff = await repo.get_by_role(UserRole.STAFF)
    first = await repo.get_by_role(UserRole.STAFF, limit=1, offset=0)
    second = await repo.get_by_role(UserRole.STAFF, limit=1, offset=1)

    assert len(staff) == 2
    assert len(first) == 1 and len(second) == 1
    assert first[0].id != second[0].id


async def test_user_repository_update_and_remove(session: AsyncSession) -> None:
    repo = UserRepository(session)
    user = await create_user(session, full_name="Before")

    user.full_name = "After"
    user.touch()
    updated = await repo.update(user)
    assert updated.full_name == "After"

    assert await repo.remove(user.id) is True
    assert await repo.get(user.id) is None
    assert await repo.remove(user.id) is False


async def test_user_repository_update_missing_raises(session: AsyncSession) -> None:
    repo = UserRepository(session)
    user = await create_user(session)
    missing_id = uuid.uuid4()
    user.id = missing_id

    try:
        await repo.update(user)
    except ValueError as exc:
        assert str(exc) == f"Entity {missing_id} not found"
    else:
        raise AssertionError("Expected ValueError")
