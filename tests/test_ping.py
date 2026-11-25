"""Tests for ping endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_ping() -> None:
    """Test ping endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/ping/")
        assert response.status_code == 200
        assert response.json() == {"message": "pong"}


@pytest.mark.asyncio
async def test_version() -> None:
    """Test version endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/v1/ping/version")
        assert response.status_code == 200
        assert response.json() == {"version": "0.1.0"}


@pytest.mark.asyncio
async def test_health() -> None:
    """Test health endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readiness() -> None:
    """Test readiness endpoint."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
