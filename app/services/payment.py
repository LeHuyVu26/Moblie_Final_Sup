"""Payment service."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.payment import get_payment_adapter
from app.domain.entities import Payment as DomainPayment
from app.domain.enums import PaymentMethod, PaymentStatus
from app.repositories.order import OrderRepository
from app.repositories.payment import PaymentRepository


class PaymentService:
    """Payment service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._payment_repo = PaymentRepository(session)
        self._order_repo = OrderRepository(session)

    async def create_payment(self, *, order_id: uuid.UUID, method: PaymentMethod) -> DomainPayment:
        """Create payment for an order."""
        existing = await self._payment_repo.get_by_order(order_id)
        if existing:
            return existing

        order = await self._order_repo.get(order_id)
        if not order:
            raise ValueError("Order not found")

        adapter = get_payment_adapter()
        result = await adapter.create_payment(order_id=order_id, amount=order.total_amount.amount, method=method)

        payment = DomainPayment(
            order_id=order_id,
            amount=order.total_amount,
            status=result.status,
            provider=method.value,
            provider_transaction_id=result.transaction_id,
            provider_response=result.provider_response,
        )
        return await self._payment_repo.add(payment)

    async def confirm_payment(self, payment_id: uuid.UUID) -> DomainPayment:
        """Confirm a payment."""
        payment = await self._payment_repo.get(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status == PaymentStatus.COMPLETED:
            return payment

        adapter = get_payment_adapter()
        if not payment.provider_transaction_id:
            raise ValueError("Payment has no transaction ID")

        result = await adapter.confirm_payment(transaction_id=payment.provider_transaction_id)
        payment.status = result.status
        payment.provider_response = result.provider_response
        if result.status == PaymentStatus.COMPLETED:
            payment.paid_at = datetime.utcnow()

        return await self._payment_repo.update(payment)

    async def refund_payment(self, payment_id: uuid.UUID) -> DomainPayment:
        """Refund a payment."""
        payment = await self._payment_repo.get(payment_id)
        if not payment:
            raise ValueError("Payment not found")

        if payment.status != PaymentStatus.COMPLETED:
            raise ValueError("Only completed payments can be refunded")

        adapter = get_payment_adapter()
        if not payment.provider_transaction_id:
            raise ValueError("Payment has no transaction ID")

        result = await adapter.refund_payment(
            transaction_id=payment.provider_transaction_id, amount=payment.amount.amount
        )
        payment.status = result.status
        payment.provider_response = result.provider_response

        return await self._payment_repo.update(payment)

    async def get_payment_by_order(self, order_id: uuid.UUID) -> DomainPayment | None:
        """Get payment by order ID."""
        return await self._payment_repo.get_by_order(order_id)
