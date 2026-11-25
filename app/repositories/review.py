"""Review repository implementation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Review as DomainReview
from app.orm.models import Review as ReviewModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import join_csv, split_csv


class ReviewRepository(BaseRepository[DomainReview, ReviewModel]):
    """Review repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ReviewModel)

    def _to_domain(self, model: ReviewModel) -> DomainReview:
        return DomainReview(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            customer_id=model.customer_id,
            restaurant_id=model.restaurant_id,
            order_id=model.order_id,
            rating=model.rating,
            comment=model.comment,
            images=split_csv(model.images),
            is_verified=model.is_verified,
        )

    def _to_model(self, entity: DomainReview) -> ReviewModel:
        return ReviewModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            customer_id=entity.customer_id,
            restaurant_id=entity.restaurant_id,
            order_id=entity.order_id,
            rating=entity.rating,
            comment=entity.comment,
            images=join_csv(entity.images),
            is_verified=entity.is_verified,
        )

    async def get_by_restaurant(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainReview]:
        stmt = (
            select(ReviewModel)
            .where(ReviewModel.restaurant_id == restaurant_id)
            .order_by(ReviewModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def get_by_order(self, order_id: uuid.UUID) -> DomainReview | None:
        stmt = select(ReviewModel).where(ReviewModel.order_id == order_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None
