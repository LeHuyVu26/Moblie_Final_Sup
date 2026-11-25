"""Database session lifecycle tests."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

import app.config.database as database_module


class FakeSession:
    """Minimal async session that records lifecycle calls."""

    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.closed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True

    async def close(self) -> None:
        self.closed = True

    async def __aenter__(self) -> FakeSession:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeConnection:
    """Minimal SQLAlchemy connection stub."""

    def __init__(self) -> None:
        self.run_sync_callback: Callable[[Any], Any] | None = None

    async def run_sync(self, callback: Callable[[Any], Any]) -> None:
        self.run_sync_callback = callback


class FakeBegin:
    """Async context manager returned by FakeEngine.begin()."""

    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self.connection

    async def __aexit__(self, *args: object) -> None:
        return None


class FakeEngine:
    """Minimal async engine stub."""

    def __init__(self) -> None:
        self.connection = FakeConnection()
        self.disposed = False

    def begin(self) -> FakeBegin:
        return FakeBegin(self.connection)

    async def dispose(self) -> None:
        self.disposed = True


async def test_get_db_commits_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Successful dependency use commits and closes the session."""
    session = FakeSession()
    monkeypatch.setattr(database_module, "async_session_maker", lambda: session)

    async with database_module.get_db() as yielded:
        assert yielded is session  # type: ignore[comparison-overlap]

    assert session.committed is True
    assert session.rolled_back is False
    assert session.closed is True


async def test_get_db_rolls_back_on_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exceptions roll back and close the session."""
    session = FakeSession()
    monkeypatch.setattr(database_module, "async_session_maker", lambda: session)

    with pytest.raises(RuntimeError, match="boom"):
        async with database_module.get_db():
            raise RuntimeError("boom")

    assert session.committed is False
    assert session.rolled_back is True
    assert session.closed is True


async def test_init_db_and_close_db(monkeypatch: pytest.MonkeyPatch) -> None:
    """Schema initialization and disposal delegate to the configured engine."""
    engine = FakeEngine()
    monkeypatch.setattr(database_module, "engine", engine)

    await database_module.init_db()

    assert engine.connection.run_sync_callback is not None

    await database_module.close_db()

    assert engine.disposed is True
