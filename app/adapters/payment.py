"""Payment gateway adapters (mock implementations)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.domain.enums import PaymentMethod, PaymentStatus


@dataclass(frozen=True, slots=True)
class PaymentResult:
    """Payment gateway result."""

    transaction_id: str
    status: PaymentStatus
    provider_response: dict[str, object]


class PaymentGatewayAdapter(Protocol):
    """Protocol for payment gateway adapters."""

    async def create_payment(self, *, order_id: uuid.UUID, amount: Decimal, method: PaymentMethod) -> PaymentResult:
        """Create payment intent."""
        ...

    async def confirm_payment(self, *, transaction_id: str) -> PaymentResult:
        """Confirm payment."""
        ...

    async def refund_payment(self, *, transaction_id: str, amount: Decimal) -> PaymentResult:
        """Refund payment."""
        ...


class MockPaymentAdapter:
    """Mock payment gateway adapter for development/testing."""

    async def create_payment(self, *, order_id: uuid.UUID, amount: Decimal, method: PaymentMethod) -> PaymentResult:
        """Create mock payment intent."""
        transaction_id = f"MOCK-PAY-{order_id.hex[:12].upper()}"
        return PaymentResult(
            transaction_id=transaction_id,
            status=PaymentStatus.PROCESSING,
            provider_response={
                "provider": "MOCK",
                "method": method.value,
                "amount": str(amount),
                "client_secret": f"mock_secret_{transaction_id}",
                "redirect_url": f"https://payment.mock.com/pay/{transaction_id}",
            },
        )

    async def confirm_payment(self, *, transaction_id: str) -> PaymentResult:
        """Confirm mock payment."""
        return PaymentResult(
            transaction_id=transaction_id,
            status=PaymentStatus.COMPLETED,
            provider_response={"provider": "MOCK", "status": "COMPLETED"},
        )

    async def refund_payment(self, *, transaction_id: str, amount: Decimal) -> PaymentResult:
        """Refund mock payment."""
        return PaymentResult(
            transaction_id=transaction_id,
            status=PaymentStatus.REFUNDED,
            provider_response={"provider": "MOCK", "status": "REFUNDED", "amount": str(amount)},
        )


def get_payment_adapter() -> PaymentGatewayAdapter:
    """Get payment gateway adapter."""
    return MockPaymentAdapter()
