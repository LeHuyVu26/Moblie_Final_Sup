"""Domain value object tests."""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.value_objects import Address, Coordinates, Money, PhoneNumber


def test_money_validates_and_quantizes_amount() -> None:
    """Money accepts valid VND amounts and quantizes to two decimals."""
    money = Money(amount=Decimal("10.5"))

    assert money.amount == Decimal("10.50")
    assert money.currency == "VND"
    assert str(money) == "10 VND"
    assert repr(money) == "Money(amount=10.50, currency=VND)"


@pytest.mark.parametrize(
    "amount",
    [Decimal("-1"), Decimal("1.234"), Decimal("1234567890123")],
)
def test_money_rejects_invalid_amounts(amount: Decimal) -> None:
    """Negative, over-precise, and oversized amounts are rejected."""
    with pytest.raises(ValidationError):
        Money(amount=amount)


def test_money_rejects_non_vnd_currency() -> None:
    """Only VND is supported."""
    with pytest.raises(ValidationError):
        Money(amount=Decimal("1"), currency="USD")


def test_money_arithmetic() -> None:
    """Money supports arithmetic with non-negative results."""
    ten = Money(amount=Decimal("10"))
    four = Money(amount=Decimal("4"))

    assert (ten + four).amount == Decimal("14.00")
    assert (ten - four).amount == Decimal("6.00")
    assert (ten * 3).amount == Decimal("30.00")
    assert (ten / 4).amount == Decimal("2.50")

    with pytest.raises(ValueError, match="Result cannot be negative"):
        _ = four - ten
    with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
        _ = ten / 0


def test_money_comparisons() -> None:
    """Money comparisons use the numeric amount."""
    ten = Money(amount=Decimal("10"))
    twenty = Money(amount=Decimal("20"))

    assert ten < twenty
    assert ten <= Money(amount=Decimal("10"))
    assert twenty > ten
    assert twenty >= Money(amount=Decimal("20"))


def test_address_full_address_and_validation() -> None:
    """Address formats its parts and validates coordinates."""
    value = Address(
        street="123 Main Street",
        ward="Ward 1",
        district="District 1",
        city="Ho Chi Minh City",
        latitude=10.0,
        longitude=106.0,
    )

    assert value.full_address() == "123 Main Street, Ward 1, District 1, Ho Chi Minh City"

    with pytest.raises(ValidationError):
        Address(street="", ward="Ward 1", district="District 1", city="City")
    with pytest.raises(ValidationError):
        Address(street="Street", ward="Ward", district="District", city="City", latitude=91)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("0912345678", "+84912345678"),
        ("84 912-345-678", "+84912345678"),
        ("+84912345678", "+84912345678"),
    ],
)
def test_phone_number_normalize(raw: str, expected: str) -> None:
    """Phone normalization handles local and international formats."""
    assert PhoneNumber.normalize(raw) == expected


def test_phone_number_validates_pattern() -> None:
    """Only supported Vietnamese prefixes are accepted."""
    assert PhoneNumber(number="+84912345678").number == "+84912345678"

    with pytest.raises(ValidationError):
        PhoneNumber(number="1234567890")


def test_coordinates_distance_to() -> None:
    """Haversine distance is approximately correct for known points."""
    hanoi = Coordinates(latitude=21.0278, longitude=105.8342)
    hcmc = Coordinates(latitude=10.8231, longitude=106.6297)

    assert hanoi.distance_to(hanoi) == pytest.approx(0.0)
    assert hanoi.distance_to(hcmc) == pytest.approx(1138.0, abs=5.0)


def test_coordinates_validate_ranges() -> None:
    """Coordinates reject out-of-range values."""
    with pytest.raises(ValidationError):
        Coordinates(latitude=91, longitude=0)
    with pytest.raises(ValidationError):
        Coordinates(latitude=0, longitude=-181)
