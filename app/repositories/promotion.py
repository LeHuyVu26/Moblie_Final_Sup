"""Promotion repository implementation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Promotion as DomainPromotion
from app.orm.models import Promotion as PromotionModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import join_csv_uuids, money, split_csv_uuids


class PromotionRepository(BaseRepository[DomainPromotion, PromotionModel]):
    """Promotion repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PromotionModel)

    def _to_domain(self, model: PromotionModel) -> DomainPromotion:
        return DomainPromotion(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            restaurant_id=model.restaurant_id,
            name=model.name,
            description=model.description,
            type=model.type,
            value=model.value,
            min_order_amount=money(model.min_order_amount),
            max_discount_amount=money(model.max_discount_amount),
            usage_limit=model.usage_limit,
            usage_count=model.usage_count,
            user_usage_limit=model.user_usage_limit,
            start_at=model.start_at,
            end_at=model.end_at,
            is_active=model.is_active,
            applicable_menu_item_ids=split_csv_uuids(model.applicable_menu_item_ids),
            applicable_category_ids=split_csv_uuids(model.applicable_category_ids),
        )

    def _to_model(self, entity: DomainPromotion) -> PromotionModel:
        return PromotionModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            restaurant_id=entity.restaurant_id,
            name=entity.name,
            description=entity.description,
            type=entity.type,
            value=entity.value,
            min_order_amount=entity.min_order_amount.amount if entity.min_order_amount else None,
            max_discount_amount=(entity.max_discount_amount.amount if entity.max_discount_amount else None),
            usage_limit=entity.usage_limit,
            usage_count=entity.usage_count,
            user_usage_limit=entity.user_usage_limit,
            start_at=entity.start_at,
            end_at=entity.end_at,
            is_active=entity.is_active,
            applicable_menu_item_ids=join_csv_uuids(entity.applicable_menu_item_ids),
            applicable_category_ids=join_csv_uuids(entity.applicable_category_ids),
        )

    async def get_by_restaurant(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainPromotion]:
        stmt = select(PromotionModel).where(PromotionModel.restaurant_id == restaurant_id).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def get_active_by_restaurant(
        self,
        restaurant_id: uuid.UUID,
        *,
        at: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DomainPromotion]:
        now = at or datetime.utcnow()
        stmt = (
            select(PromotionModel)
            .where(
                PromotionModel.restaurant_id == restaurant_id,
                PromotionModel.is_active.is_(True),
                PromotionModel.start_at <= now,
                PromotionModel.end_at >= now,
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]
