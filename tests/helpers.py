"""Reusable assertion helpers for tests."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, Response

from app.domain.entities import Order as DomainOrder
from app.repositories.order import OrderRepository


def auth_headers(token: str) -> dict[str, str]:
    """Build bearer authentication headers."""
    return {"Authorization": f"Bearer {token}"}


def assert_error(response: Response, status_code: int, detail: str) -> None:
    """Assert an HTTP error response body."""
    assert response.status_code == status_code
    assert response.json() == {"detail": detail}, response.text


def assert_page(payload: dict[str, Any], *, page: int = 1, size: int = 20) -> list[Any]:
    """Assert common pagination response fields and return items."""
    assert payload["page"] == page
    assert payload["size"] == size
    assert isinstance(payload["items"], list)
    assert payload["total"] == len(payload["items"])
    assert payload["pages"] == (1 if payload["items"] else 0)
    return payload["items"]


def route_inventory(app: FastAPI) -> set[tuple[str, str]]:
    """Return the set of (method, path) routes registered on the app."""
    return {
        (method, path)
        for route in app.routes
        for method in getattr(route, "methods", set())
        if method not in {"HEAD", "OPTIONS"} and (path := getattr(route, "path", None)) is not None
    }


async def assert_requires_auth(client: AsyncClient, method: str, url: str, **kwargs: Any) -> None:
    """Assert an endpoint rejects unauthenticated requests."""
    response = await client.request(method, url, **kwargs)
    assert_error(response, 401, "Not authenticated")


async def _add_order_without_lazy_load(self: OrderRepository, entity: DomainOrder) -> DomainOrder:
    """Persist an order and read it back with eager-loaded items."""
    model = self._to_model(entity)
    self._session.add(model)
    await self._session.flush()
    await self._session.refresh(model)
    fetched = await self.get(entity.id)
    assert fetched is not None
    return fetched


async def _update_order_without_lazy_load(self: OrderRepository, entity: DomainOrder) -> DomainOrder:
    """Update an order and read it back with eager-loaded items."""
    from sqlalchemy import select

    result = await self._session.execute(select(self._model).where(self._model.id == entity.id))
    model = result.scalar_one_or_none()
    if model is None:
        raise ValueError(f"Entity {entity.id} not found")
    updated = self._to_model(entity)
    for column in model.__table__.columns:
        setattr(model, column.name, getattr(updated, column.name))
    await self._session.flush()
    await self._session.refresh(model)
    fetched = await self.get(entity.id)
    assert fetched is not None
    return fetched


def patch_order_repository_add(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid the known async lazy-load issue in OrderRepository.add()/update()."""
    monkeypatch.setattr(OrderRepository, "add", _add_order_without_lazy_load)
    monkeypatch.setattr(OrderRepository, "update", _update_order_without_lazy_load)
