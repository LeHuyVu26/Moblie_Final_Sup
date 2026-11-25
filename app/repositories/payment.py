"""Payment repository implementation."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Payment as DomainPayment
from app.orm.models import Payment as PaymentModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import dumps_json, loads_json, money_required


class PaymentRepository(BaseRepository[DomainPayment, PaymentModel]):
    """Payment repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PaymentModel)

    def _to_domain(self, model: PaymentModel) -> DomainPayment:
        return DomainPayment(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            order_id=model.order_id,
            amount=money_required(model.amount),
            status=model.status,
            provider=model.provider,
            provider_transaction_id=model.provider_transaction_id,
            provider_response=loads_json(model.provider_response),
            paid_at=model.paid_at,
            failed_at=model.failed_at,
            failure_reason=model.failure_reason,
        )

    def _to_model(self, entity: DomainPayment) -> PaymentModel:
        return PaymentModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            order_id=entity.order_id,
            amount=entity.amount.amount,
            status=entity.status,
            provider=entity.provider,
            provider_transaction_id=entity.provider_transaction_id,
            provider_response=dumps_json(entity.provider_response),
            paid_at=entity.paid_at,
            failed_at=entity.failed_at,
            failure_reason=entity.failure_reason,
        )

    async def get_by_order(self, order_id: uuid.UUID) -> DomainPayment | None:
        stmt = select(PaymentModel).where(PaymentModel.order_id == order_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None
