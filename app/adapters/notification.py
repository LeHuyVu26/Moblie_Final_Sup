"""Notification adapters (mock implementations)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.domain.enums import DeliveryStatus, OrderStatus


@dataclass(frozen=True, slots=True)
class NotificationResult:
    """Notification result."""

    success: bool
    message_id: str | None = None


class NotificationAdapter(Protocol):
    """Protocol for notification adapters."""

    async def send_order_status(
        self, *, user_id: uuid.UUID, order_id: uuid.UUID, status: OrderStatus
    ) -> NotificationResult:
        """Send order status notification."""
        ...

    async def send_delivery_status(
        self, *, user_id: uuid.UUID, order_id: uuid.UUID, status: DeliveryStatus
    ) -> NotificationResult:
        """Send delivery status notification."""
        ...


class MockNotificationAdapter:
    """Mock notification adapter for development/testing."""

    async def send_order_status(
        self, *, user_id: uuid.UUID, order_id: uuid.UUID, status: OrderStatus
    ) -> NotificationResult:
        """Send mock order status notification."""
        return NotificationResult(success=True, message_id=f"MOCK-ORDER-{order_id.hex[:12].upper()}-{status.value}")

    async def send_delivery_status(
        self, *, user_id: uuid.UUID, order_id: uuid.UUID, status: DeliveryStatus
    ) -> NotificationResult:
        """Send mock delivery status notification."""
        return NotificationResult(success=True, message_id=f"MOCK-DELIVERY-{order_id.hex[:12].upper()}-{status.value}")


def get_notification_adapter() -> NotificationAdapter:
    """Get notification adapter."""
    return MockNotificationAdapter()
