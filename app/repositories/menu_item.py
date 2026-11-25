"""Menu item repository implementation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import MenuItem as DomainMenuItem
from app.domain.enums import MenuItemStatus
from app.orm.models import MenuItem as MenuItemModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import join_csv, money, money_required, split_csv


class MenuItemRepository(BaseRepository[DomainMenuItem, MenuItemModel]):
    """Menu item repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MenuItemModel)

    def _to_domain(self, model: MenuItemModel) -> DomainMenuItem:
        return DomainMenuItem(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            restaurant_id=model.restaurant_id,
            category_id=model.category_id,
            name=model.name,
            description=model.description,
            price=money_required(model.price),
            original_price=money(model.original_price),
            image_url=model.image_url,
            status=model.status,
            is_vegetarian=model.is_vegetarian,
            is_vegan=model.is_vegan,
            is_spicy=model.is_spicy,
            preparation_time_minutes=model.preparation_time_minutes,
            calories=model.calories,
            allergens=split_csv(model.allergens),
            display_order=model.display_order,
        )

    def _to_model(self, entity: DomainMenuItem) -> MenuItemModel:
        return MenuItemModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            restaurant_id=entity.restaurant_id,
            category_id=entity.category_id,
            name=entity.name,
            description=entity.description,
            price=entity.price.amount,
            original_price=entity.original_price.amount if entity.original_price else None,
            image_url=entity.image_url,
            status=entity.status,
            is_vegetarian=entity.is_vegetarian,
            is_vegan=entity.is_vegan,
            is_spicy=entity.is_spicy,
            preparation_time_minutes=entity.preparation_time_minutes,
            calories=entity.calories,
            allergens=join_csv(entity.allergens),
            display_order=entity.display_order,
        )

    async def get_by_restaurant(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainMenuItem]:
        stmt = (
            select(MenuItemModel)
            .where(MenuItemModel.restaurant_id == restaurant_id)
            .order_by(MenuItemModel.display_order)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def get_by_category(
        self, category_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainMenuItem]:
        stmt = (
            select(MenuItemModel)
            .where(MenuItemModel.category_id == category_id)
            .order_by(MenuItemModel.display_order)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]

    async def get_available_by_restaurant(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainMenuItem]:
        stmt = (
            select(MenuItemModel)
            .where(
                MenuItemModel.restaurant_id == restaurant_id,
                MenuItemModel.status == MenuItemStatus.AVAILABLE,
            )
            .order_by(MenuItemModel.display_order)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]
