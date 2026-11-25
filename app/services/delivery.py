"""Delivery service."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.delivery import get_delivery_adapter
from app.domain.entities import Delivery as DomainDelivery
from app.domain.enums import DeliveryProvider, DeliveryStatus, OrderStatus
from app.domain.value_objects import Address, Coordinates, PhoneNumber
from app.repositories.delivery import DeliveryRepository
from app.repositories.order import OrderRepository
from app.repositories.restaurant import RestaurantRepository


class DeliveryService:
    """Delivery service for dispatch and tracking."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._delivery_repo = DeliveryRepository(session)
        self._order_repo = OrderRepository(session)
        self._restaurant_repo = RestaurantRepository(session)

    async def get_quote(
        self,
        *,
        pickup: Address,
        dropoff: Address,
        provider: DeliveryProvider = DeliveryProvider.AHAMOVE,
        pickup_coordinates: Coordinates | None = None,
        dropoff_coordinates: Coordinates | None = None,
    ) -> dict[str, object]:
        """Get delivery quote from provider."""
        adapter = get_delivery_adapter(provider)
        quote = await adapter.get_quote(
            pickup=pickup,
            dropoff=dropoff,
            pickup_coordinates=pickup_coordinates,
            dropoff_coordinates=dropoff_coordinates,
        )
        return {
            "provider": quote.provider.value,
            "fee": quote.fee,
            "distance_km": quote.distance_km,
            "estimated_duration_minutes": quote.estimated_duration_minutes,
        }

    async def auto_dispatch(
        self, order_id: uuid.UUID, provider: DeliveryProvider = DeliveryProvider.AHAMOVE
    ) -> DomainDelivery:
        """Automatically dispatch delivery for an order."""
        # Check if delivery already exists
        existing = await self._delivery_repo.get_by_order(order_id)
        if existing:
            return existing

        order = await self._order_repo.get(order_id)
        if not order:
            raise ValueError("Order not found")
        if order.status != OrderStatus.READY_FOR_PICKUP:
            raise ValueError("Order is not ready for pickup")

        restaurant = await self._restaurant_repo.get(order.restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")

        # Create delivery
        delivery = DomainDelivery(
            order_id=order_id,
            provider=provider,
            pickup_address=restaurant.address,
            pickup_coordinates=(
                Coordinates(
                    latitude=restaurant.address.latitude,
                    longitude=restaurant.address.longitude,
                )
                if restaurant.address.latitude is not None and restaurant.address.longitude is not None
                else None
            ),
            dropoff_address=order.delivery_address,
            dropoff_coordinates=order.delivery_coordinates,
            fee=order.delivery_fee,
        )

        saved_delivery = await self._delivery_repo.add(delivery)

        # Create booking with provider
        adapter = get_delivery_adapter(provider)
        booking = await adapter.create_booking(
            order_id=order_id,
            pickup=restaurant.address,
            dropoff=order.delivery_address,
            pickup_coordinates=delivery.pickup_coordinates,
            dropoff_coordinates=order.delivery_coordinates,
            cod_amount=order.total_amount.amount if order.total_amount else None,
            notes=order.customer_note,
        )

        # Update delivery with booking info
        saved_delivery.provider_order_id = booking.provider_order_id
        saved_delivery.status = booking.status
        saved_delivery.driver_name = booking.driver_name
        saved_delivery.driver_phone = (
            PhoneNumber(number=PhoneNumber.normalize(booking.driver_phone)) if booking.driver_phone else None
        )
        saved_delivery.driver_vehicle = booking.driver_vehicle
        saved_delivery.driver_license_plate = booking.driver_license_plate
        saved_delivery.tracking_url = booking.tracking_url
        saved_delivery.assigned_at = datetime.utcnow()

        return await self._delivery_repo.update(saved_delivery)

    async def get_delivery(self, delivery_id: uuid.UUID) -> DomainDelivery | None:
        """Get delivery by ID."""
        return await self._delivery_repo.get(delivery_id)

    async def get_delivery_by_order(self, order_id: uuid.UUID) -> DomainDelivery | None:
        """Get delivery by order ID."""
        return await self._delivery_repo.get_by_order(order_id)

    async def update_delivery_status(self, delivery_id: uuid.UUID, new_status: DeliveryStatus) -> DomainDelivery:
        """Update delivery status."""
        delivery = await self._delivery_repo.get(delivery_id)
        if not delivery:
            raise ValueError("Delivery not found")

        if not delivery.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {delivery.status} to {new_status}")

        delivery.transition_to(new_status)
        return await self._delivery_repo.update(delivery)

    async def update_tracking(
        self,
        order_id: uuid.UUID,
        *,
        status: DeliveryStatus,
        driver_name: str | None = None,
        driver_phone: str | None = None,
        tracking_url: str | None = None,
    ) -> DomainDelivery:
        """Update delivery tracking information."""
        delivery = await self._delivery_repo.get_by_order(order_id)
        if not delivery:
            raise ValueError("Delivery not found")

        if driver_name:
            delivery.driver_name = driver_name
        if driver_phone:
            delivery.driver_phone = PhoneNumber(number=PhoneNumber.normalize(driver_phone))
        if tracking_url:
            delivery.tracking_url = tracking_url

        if status != delivery.status:
            if not delivery.can_transition_to(status):
                raise ValueError(f"Cannot transition from {delivery.status} to {status}")
            delivery.transition_to(status)

        return await self._delivery_repo.update(delivery)
