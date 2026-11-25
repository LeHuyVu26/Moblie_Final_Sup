"""Delivery provider adapters (mock implementations)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.domain.enums import DeliveryProvider, DeliveryStatus
from app.domain.value_objects import Address, Coordinates


@dataclass(frozen=True, slots=True)
class DeliveryQuote:
    """Delivery quote from provider."""

    provider: DeliveryProvider
    fee: Decimal
    distance_km: Decimal
    estimated_duration_minutes: int


@dataclass(frozen=True, slots=True)
class DeliveryBooking:
    """Delivery booking result from provider."""

    provider_order_id: str
    status: DeliveryStatus
    driver_name: str | None = None
    driver_phone: str | None = None
    driver_vehicle: str | None = None
    driver_license_plate: str | None = None
    tracking_url: str | None = None
    estimated_pickup_at: str | None = None
    estimated_dropoff_at: str | None = None


class DeliveryProviderAdapter(Protocol):
    """Protocol for delivery provider adapters."""

    async def get_quote(
        self,
        *,
        pickup: Address,
        dropoff: Address,
        pickup_coordinates: Coordinates | None = None,
        dropoff_coordinates: Coordinates | None = None,
    ) -> DeliveryQuote:
        """Get delivery quote."""
        ...

    async def create_booking(
        self,
        *,
        order_id: uuid.UUID,
        pickup: Address,
        dropoff: Address,
        pickup_coordinates: Coordinates | None = None,
        dropoff_coordinates: Coordinates | None = None,
        cod_amount: Decimal | None = None,
        notes: str | None = None,
    ) -> DeliveryBooking:
        """Create delivery booking."""
        ...


class MockDeliveryAdapter:
    """Mock delivery provider adapter for development/testing."""

    def __init__(self, provider: DeliveryProvider) -> None:
        self.provider = provider

    async def get_quote(
        self,
        *,
        pickup: Address,
        dropoff: Address,
        pickup_coordinates: Coordinates | None = None,
        dropoff_coordinates: Coordinates | None = None,
    ) -> DeliveryQuote:
        """Get mock delivery quote based on distance."""
        # Calculate distance if coordinates available
        if pickup_coordinates and dropoff_coordinates:
            distance = Decimal(str(pickup_coordinates.distance_to(dropoff_coordinates)))
        else:
            distance = Decimal("3.0")  # default 3km

        # Fee = base fee + distance fee
        base_fee = Decimal("15000")
        per_km = Decimal("5000")
        fee = base_fee + (distance * per_km)

        # Duration = 10 min base + 5 min per km
        duration = int(10 + (distance * Decimal("5")))

        return DeliveryQuote(
            provider=self.provider,
            fee=fee.quantize(Decimal("1")),
            distance_km=distance.quantize(Decimal("0.1")),
            estimated_duration_minutes=duration,
        )

    async def create_booking(
        self,
        *,
        order_id: uuid.UUID,
        pickup: Address,
        dropoff: Address,
        pickup_coordinates: Coordinates | None = None,
        dropoff_coordinates: Coordinates | None = None,
        cod_amount: Decimal | None = None,
        notes: str | None = None,
    ) -> DeliveryBooking:
        """Create mock delivery booking."""
        return DeliveryBooking(
            provider_order_id=f"MOCK-{self.provider.value}-{order_id.hex[:12].upper()}",
            status=DeliveryStatus.DRIVER_ASSIGNED,
            driver_name="Nguyễn Văn A (Mock)",
            driver_phone="0901234567",
            driver_vehicle="Xe máy",
            driver_license_plate="51B-12345",
            tracking_url=f"https://tracking.mock.com/{self.provider.value.lower()}/{order_id}",
        )


def get_delivery_adapter(provider: DeliveryProvider) -> DeliveryProviderAdapter:
    """Get delivery provider adapter."""
    return MockDeliveryAdapter(provider)
