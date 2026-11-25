"""Order repository implementation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities import Order as DomainOrder
from app.domain.entities import OrderItem as DomainOrderItem
from app.domain.enums import OrderStatus
from app.orm.models import Order as OrderModel
from app.orm.models import OrderItem as OrderItemModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import address, coordinates, money_required


class OrderRepository(BaseRepository[DomainOrder, OrderModel]):
    """Order repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OrderModel)

    def _item_to_domain(self, model: OrderItemModel) -> DomainOrderItem:
        return DomainOrderItem(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            order_id=model.order_id,
            menu_item_id=model.menu_item_id,
            menu_item_name=model.menu_item_name,
            menu_item_price=money_required(model.menu_item_price),
            quantity=model.quantity,
            note=model.note,
            subtotal=money_required(model.subtotal),
        )

    def _item_to_model(self, entity: DomainOrderItem) -> OrderItemModel:
        return OrderItemModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            order_id=entity.order_id,
            menu_item_id=entity.menu_item_id,
            menu_item_name=entity.menu_item_name,
            menu_item_price=entity.menu_item_price.amount,
            quantity=entity.quantity,
            note=entity.note,
            subtotal=entity.subtotal.amount,
        )

    def _to_domain(self, model: OrderModel) -> DomainOrder:
        items = [self._item_to_domain(item) for item in getattr(model, "items", []) or []]
        return DomainOrder(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            customer_id=model.customer_id,
            restaurant_id=model.restaurant_id,
            status=model.status,
            items=items,
            subtotal=money_required(model.subtotal),
            delivery_fee=money_required(model.delivery_fee),
            discount_amount=money_required(model.discount_amount),
            total_amount=money_required(model.total_amount),
            promotion_id=model.promotion_id,
            promotion_code=model.promotion_code,
            delivery_address=address(
                street=model.street,
                ward=model.ward,
                district=model.district,
                city=model.city,
                latitude=model.latitude,
                longitude=model.longitude,
            ),
            delivery_coordinates=coordinates(model.latitude, model.longitude),
            customer_note=model.customer_note,
            restaurant_note=model.restaurant_note,
            estimated_preparation_time_minutes=model.estimated_preparation_time_minutes,
            confirmed_at=model.confirmed_at,
            ready_at=model.ready_at,
            dispatched_at=model.dispatched_at,
            delivered_at=model.delivered_at,
            cancelled_at=model.cancelled_at,
            cancellation_reason=model.cancellation_reason,
        )

    def _to_model(self, entity: DomainOrder) -> OrderModel:
        model = OrderModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            customer_id=entity.customer_id,
            restaurant_id=entity.restaurant_id,
            status=entity.status,
            subtotal=entity.subtotal.amount,
            delivery_fee=entity.delivery_fee.amount,
            discount_amount=entity.discount_amount.amount,
            total_amount=entity.total_amount.amount,
            promotion_id=entity.promotion_id,
            promotion_code=entity.promotion_code,
            street=entity.delivery_address.street,
            ward=entity.delivery_address.ward,
            district=entity.delivery_address.district,
            city=entity.delivery_address.city,
            latitude=entity.delivery_address.latitude,
            longitude=entity.delivery_address.longitude,
            customer_note=entity.customer_note,
            restaurant_note=entity.restaurant_note,
            estimated_preparation_time_minutes=entity.estimated_preparation_time_minutes,
            confirmed_at=entity.confirmed_at,
            ready_at=entity.ready_at,
            dispatched_at=entity.dispatched_at,
            delivered_at=entity.delivered_at,
            cancelled_at=entity.cancelled_at,
            cancellation_reason=entity.cancellation_reason,
        )
        model.items = [self._item_to_model(item) for item in entity.items]
        return model
    
    async def add(self, entity: DomainOrder) -> DomainOrder:
        """Add order and eagerly load its items."""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()

        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == model.id)
        )
        result = await self._session.execute(stmt)
        saved_model = result.scalar_one()
        return self._to_domain(saved_model)
    
    async def update(self, entity: DomainOrder) -> DomainOrder:
        """Update order and eagerly load its items."""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == entity.id)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Entity {entity.id} not found")
        updated = self._to_model(entity)
        for column in model.__table__.columns:
            setattr(model, column.name, getattr(updated, column.name))
        await self._session.flush()
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == entity.id)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(stmt)
        saved_model = result.scalar_one()
        return self._to_domain(saved_model)
    
    async def get(self, entity_id: uuid.UUID) -> DomainOrder | None:
        stmt = select(OrderModel).options(selectinload(OrderModel.items)).where(OrderModel.id == entity_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_all(self, *, limit: int = 100, offset: int = 0) -> list[DomainOrder]:
        stmt = select(OrderModel).options(selectinload(OrderModel.items)).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().unique().all()]

    async def get_by_customer(self, customer_id: uuid.UUID, *, limit: int = 100, offset: int = 0) -> list[DomainOrder]:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.customer_id == customer_id)
            .order_by(OrderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().unique().all()]

    async def get_by_restaurant(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainOrder]:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.restaurant_id == restaurant_id)
            .order_by(OrderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().unique().all()]

    async def get_by_status(self, status: OrderStatus, *, limit: int = 100, offset: int = 0) -> list[DomainOrder]:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.status == status)
            .order_by(OrderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().unique().all()]