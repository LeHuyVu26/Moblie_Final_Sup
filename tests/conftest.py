"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Iterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.orm.models as _orm_models  # noqa: F401  (register models on metadata)
from app.api.deps.auth import get_current_user
from app.config.database import get_session
from app.domain.entities import User
from app.domain.enums import UserRole
from app.main import app
from app.orm.base import Base
from tests.factories import create_user

TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(autouse=True)
async def prepare_database() -> AsyncGenerator[None, None]:
    """Create a fresh in-memory database for each test."""
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session bound to the test database."""
    async with test_session_maker() as db_session:
        yield db_session


ClientFactory = Callable[[User | None], AsyncClient]


@pytest.fixture
def client_factory(session: AsyncSession) -> Iterator[ClientFactory]:
    """Build an HTTP client with optional authenticated user override."""

    def factory(user: User | None = None) -> AsyncClient:
        async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
            yield session

        app.dependency_overrides[get_session] = override_get_session
        if user is None:
            app.dependency_overrides.pop(get_current_user, None)
        else:

            async def override_current_user() -> User:
                return user

            app.dependency_overrides[get_current_user] = override_current_user

        return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    yield factory
    app.dependency_overrides.clear()


@pytest.fixture
async def staff_user(session: AsyncSession) -> User:
    return await create_user(
        session,
        email="staff@example.com",
        phone="0912345678",
        full_name="Staff User",
        role=UserRole.STAFF,
    )


@pytest.fixture
async def owner_user(session: AsyncSession) -> User:
    return await create_user(
        session,
        email="owner@example.com",
        phone="0912345679",
        full_name="Owner User",
        role=UserRole.OWNER,
    )


@pytest.fixture
async def customer_user(session: AsyncSession) -> User:
    return await create_user(
        session,
        email="customer@example.com",
        phone="0912345680",
        full_name="Customer User",
        role=UserRole.CUSTOMER,
    )


@pytest.fixture
async def client(client_factory: ClientFactory, staff_user: User) -> AsyncGenerator[AsyncClient, None]:
    """Default authenticated client using the staff user."""
    async with client_factory(staff_user) as http_client:
        yield http_client
