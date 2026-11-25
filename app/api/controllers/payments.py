"""Payment controller."""

from collections.abc import Callable
from typing import Any, TypeVar, cast
from uuid import UUID

from fastapi import HTTPException, status
from fastapi_controller import controller

from app.api.controllers.base import BaseController
from app.api.deps.auth import CurrentUser, DbSession
from app.api.mappers import map_payment
from app.api.schemas.payments import PaymentMethodSelection, PaymentResponse
from app.services.payment import PaymentService

F = TypeVar("F", bound=Callable[..., Any])


def typed_get(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.get."""
    return cast(Callable[[F], F], controller.get(path))


def typed_post(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.post."""
    return cast(Callable[[F], F], controller.post(path))


class PaymentController(BaseController):  # type: ignore[misc]
    """Payment endpoints."""

    @typed_post("/{order_id}/payments")
    async def create_payment(
        self, order_id: UUID, request: PaymentMethodSelection, session: DbSession, current_user: CurrentUser
    ) -> PaymentResponse:
        """Create payment for an order."""
        service = PaymentService(session)
        try:
            payment = await service.create_payment(order_id=order_id, method=request.method)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return map_payment(payment)

    @typed_get("/{order_id}/payments")
    async def get_payment(self, order_id: UUID, session: DbSession, current_user: CurrentUser) -> PaymentResponse:
        """Get payment for an order."""
        service = PaymentService(session)
        payment = await service.get_payment_by_order(order_id)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        return map_payment(payment)

    @typed_post("/payments/{payment_id}/confirm")
    async def confirm_payment(self, payment_id: UUID, session: DbSession, current_user: CurrentUser) -> PaymentResponse:
        """Confirm a payment."""
        service = PaymentService(session)
        try:
            payment = await service.confirm_payment(payment_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return map_payment(payment)

    @typed_post("/payments/{payment_id}/refund")
    async def refund_payment(self, payment_id: UUID, session: DbSession, current_user: CurrentUser) -> PaymentResponse:
        """Refund a payment."""
        service = PaymentService(session)
        try:
            payment = await service.refund_payment(payment_id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return map_payment(payment)
