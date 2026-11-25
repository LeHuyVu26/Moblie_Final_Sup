"""Repository integration tests."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User
from app.domain.enums import UserRole
from app.domain.value_objects import PhoneNumber
from app.repositories.user import UserRepository


async def test_user_repository_round_trip(session: AsyncSession) -> None:
    """A user can be added, fetched, updated, and removed."""
    repo = UserRepository(session)
    user = User(
        email="customer@example.com",
        phone=PhoneNumber(number=PhoneNumber.normalize("0912345678")),
        full_name="Customer",
        password_hash="hashed",
        role=UserRole.CUSTOMER,
    )

    saved = await repo.add(user)
    assert saved.id == user.id

    fetched = await repo.get_by_email("customer@example.com")
    assert fetched is not None
    assert fetched.full_name == "Customer"
    assert fetched.phone.number == "+84912345678"

    fetched.full_name = "Updated Customer"
    updated = await repo.update(fetched)
    assert updated.full_name == "Updated Customer"

    assert await repo.remove(user.id) is True
    assert await repo.get(user.id) is None
