"""Category repository implementation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Category as DomainCategory
from app.orm.models import Category as CategoryModel
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[DomainCategory, CategoryModel]):
    """Category repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CategoryModel)

    def _to_domain(self, model: CategoryModel) -> DomainCategory:
        return DomainCategory(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            restaurant_id=model.restaurant_id,
            name=model.name,
            description=model.description,
            image_url=model.image_url,
            display_order=model.display_order,
            is_active=model.is_active,
        )

    def _to_model(self, entity: DomainCategory) -> CategoryModel:
        return CategoryModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            restaurant_id=entity.restaurant_id,
            name=entity.name,
            description=entity.description,
            image_url=entity.image_url,
            display_order=entity.display_order,
            is_active=entity.is_active,
        )

    async def get_by_restaurant(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainCategory]:
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.restaurant_id == restaurant_id)
            .order_by(CategoryModel.display_order)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]
