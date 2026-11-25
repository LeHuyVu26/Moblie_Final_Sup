"""Delivery repository implementation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Delivery as DomainDelivery
from app.domain.enums import DeliveryStatus
from app.orm.models import Delivery as DeliveryModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import address, coordinates, money_required, phone_optional


class DeliveryRepository(BaseRepository[DomainDelivery, DeliveryModel]):
    """Delivery repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DeliveryModel)

    def _to_domain(self, model: DeliveryModel) -> DomainDelivery:
        return DomainDelivery(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            order_id=model.order_id,
            provider=model.provider,
            provider_order_id=model.provider_order_id,
            status=model.status,
            driver_name=model.driver_name,
            driver_phone=phone_optional(model.driver_phone),
            driver_vehicle=model.driver_vehicle,
            driver_license_plate=model.driver_license_plate,
            driver_current_location=coordinates(model.driver_current_latitude, model.driver_current_longitude),
            pickup_address=address(
                street=model.pickup_street,
                ward=model.pickup_ward,
                district=model.pickup_district,
                city=model.pickup_city,
                latitude=model.pickup_latitude,
                longitude=model.pickup_longitude,
            ),
            pickup_coordinates=coordinates(model.pickup_latitude, model.pickup_longitude),
            dropoff_address=address(
                street=model.dropoff_street,
                ward=model.dropoff_ward,
                district=model.dropoff_district,
                city=model.dropoff_city,
                latitude=model.dropoff_latitude,
                longitude=model.dropoff_longitude,
            ),
            dropoff_coordinates=coordinates(model.dropoff_latitude, model.dropoff_longitude),
            distance_km=model.distance_km,
            estimated_duration_minutes=model.estimated_duration_minutes,
            fee=money_required(model.fee),
            assigned_at=model.assigned_at,
            picked_up_at=model.picked_up_at,
            delivered_at=model.delivered_at,
            failed_at=model.failed_at,
            failure_reason=model.failure_reason,
            tracking_url=model.tracking_url,
        )

    def _to_model(self, entity: DomainDelivery) -> DeliveryModel:
        return DeliveryModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            order_id=entity.order_id,
            provider=entity.provider,
            provider_order_id=entity.provider_order_id,
            status=entity.status,
            driver_name=entity.driver_name,
            driver_phone=entity.driver_phone.number if entity.driver_phone else None,
            driver_vehicle=entity.driver_vehicle,
            driver_license_plate=entity.driver_license_plate,
            driver_current_latitude=(
                entity.driver_current_location.latitude if entity.driver_current_location else None
            ),
            driver_current_longitude=(
                entity.driver_current_location.longitude if entity.driver_current_location else None
            ),
            pickup_street=entity.pickup_address.street,
            pickup_ward=entity.pickup_address.ward,
            pickup_district=entity.pickup_address.district,
            pickup_city=entity.pickup_address.city,
            pickup_latitude=entity.pickup_address.latitude,
            pickup_longitude=entity.pickup_address.longitude,
            dropoff_street=entity.dropoff_address.street,
            dropoff_ward=entity.dropoff_address.ward,
            dropoff_district=entity.dropoff_address.district,
            dropoff_city=entity.dropoff_address.city,
            dropoff_latitude=entity.dropoff_address.latitude,
            dropoff_longitude=entity.dropoff_address.longitude,
            distance_km=entity.distance_km,
            estimated_duration_minutes=entity.estimated_duration_minutes,
            fee=entity.fee.amount,
            assigned_at=entity.assigned_at,
            picked_up_at=entity.picked_up_at,
            delivered_at=entity.delivered_at,
            failed_at=entity.failed_at,
            failure_reason=entity.failure_reason,
            tracking_url=entity.tracking_url,
        )

    async def get_by_order(self, order_id: uuid.UUID) -> DomainDelivery | None:
        stmt = select(DeliveryModel).where(DeliveryModel.order_id == order_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_status(self, status: DeliveryStatus, *, limit: int = 100, offset: int = 0) -> list[DomainDelivery]:
        stmt = select(DeliveryModel).where(DeliveryModel.status == status).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]
