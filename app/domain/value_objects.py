"""Value objects for the domain."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator, Field

from app.domain.base import ValueObject


def _validate_vnd_amount(value: Decimal) -> Decimal:
    """Validate VND amount: non-negative, max 2 decimal places, max 12 digits."""
    if value < 0:
        raise ValueError("Amount cannot be negative")
    # Check decimal places - exponent is negative for decimal places
    exp = value.as_tuple().exponent
    if isinstance(exp, int) and exp < -2:
        raise ValueError("Amount cannot have more than 2 decimal places")
    # Check total digits (max 12 digits total)
    digits = len(str(value).replace(".", "").replace("-", ""))
    if digits > 12:
        raise ValueError("Amount cannot exceed 12 digits total")
    # Quantize to 2 decimal places
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


VndAmount = Annotated[Decimal, AfterValidator(_validate_vnd_amount)]


class Money(ValueObject):
    """Money value object for VND currency."""

    amount: VndAmount = Field(..., description="Amount in VND")
    currency: str = Field(default="VND", pattern="^VND$")

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount)

    def __sub__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(amount=result)

    def __mul__(self, multiplier: int | Decimal) -> Money:
        if not isinstance(multiplier, int | Decimal):
            return NotImplemented
        return Money(amount=self.amount * multiplier)

    def __truediv__(self, divisor: int | Decimal) -> Money:
        if not isinstance(divisor, int | Decimal):
            return NotImplemented
        if divisor == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return Money(amount=self.amount / divisor)

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount <= other.amount

    def __gt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount >= other.amount

    def __str__(self) -> str:
        return f"{self.amount:,.0f} {self.currency}"

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency={self.currency})"


class Address(ValueObject):
    """Address value object."""

    street: str = Field(..., min_length=1, max_length=200)
    ward: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    def full_address(self) -> str:
        """Return formatted full address."""
        parts = [self.street, self.ward, self.district, self.city]
        return ", ".join(parts)


class PhoneNumber(ValueObject):
    """Vietnamese phone number value object."""

    number: str = Field(..., pattern=r"^(?:\+84|0)(?:3|5|7|8|9)\d{8}$")

    @classmethod
    def normalize(cls, phone: str) -> str:
        """Normalize phone number to +84 format."""
        phone = phone.strip().replace(" ", "").replace("-", "")
        if phone.startswith("0"):
            return "+84" + phone[1:]
        if phone.startswith("84"):
            return "+" + phone
        if phone.startswith("+84"):
            return phone
        return "+84" + phone


class Coordinates(ValueObject):
    """GPS coordinates value object."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    def distance_to(self, other: Coordinates) -> float:
        """Calculate approximate distance in kilometers using Haversine formula."""
        from math import atan2, cos, radians, sin, sqrt

        R = 6371  # Earth radius in km
        lat1, lon1 = radians(self.latitude), radians(self.longitude)
        lat2, lon2 = radians(other.latitude), radians(other.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c
