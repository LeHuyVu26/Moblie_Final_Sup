"""Restaurant repository implementation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Restaurant as DomainRestaurant
from app.orm.models import Restaurant as RestaurantModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import address, money_required, phone


class RestaurantRepository(BaseRepository[DomainRestaurant, RestaurantModel]):
    """Restaurant repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RestaurantModel)

    def _to_domain(self, model: RestaurantModel) -> DomainRestaurant:
        return DomainRestaurant(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            owner_id=model.owner_id,
            name=model.name,
            description=model.description,
            address=address(
                street=model.street,
                ward=model.ward,
                district=model.district,
                city=model.city,
                latitude=model.latitude,
                longitude=model.longitude,
            ),
            phone=phone(model.phone),
            email=model.email,
            logo_url=model.logo_url,
            cover_image_url=model.cover_image_url,
            is_active=model.is_active,
            opening_time=model.opening_time,
            closing_time=model.closing_time,
            min_order_amount=money_required(model.min_order_amount),
            delivery_fee=money_required(model.delivery_fee),
            delivery_radius_km=model.delivery_radius_km,
            rating=model.rating,
            total_reviews=model.total_reviews,
        )

    def _to_model(self, entity: DomainRestaurant) -> RestaurantModel:
        return RestaurantModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            owner_id=entity.owner_id,
            name=entity.name,
            description=entity.description,
            street=entity.address.street,
            ward=entity.address.ward,
            district=entity.address.district,
            city=entity.address.city,
            latitude=entity.address.latitude,
            longitude=entity.address.longitude,
            phone=entity.phone.number,
            email=entity.email,
            logo_url=entity.logo_url,
            cover_image_url=entity.cover_image_url,
            is_active=entity.is_active,
            opening_time=entity.opening_time,
            closing_time=entity.closing_time,
            min_order_amount=entity.min_order_amount.amount,
            delivery_fee=entity.delivery_fee.amount,
            delivery_radius_km=entity.delivery_radius_km,
            rating=entity.rating,
            total_reviews=entity.total_reviews,
        )

    async def get_by_owner(self, owner_id: uuid.UUID, *, limit: int = 100, offset: int = 0) -> list[DomainRestaurant]:
        stmt = select(RestaurantModel).where(RestaurantModel.owner_id == owner_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def list_active(self, *, limit: int = 100, offset: int = 0) -> list[DomainRestaurant]:
        stmt = select(RestaurantModel).where(RestaurantModel.is_active.is_(True)).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]
