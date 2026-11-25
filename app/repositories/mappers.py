"""Shared mapping helpers between ORM and domain."""

from __future__ import annotations

import json
import uuid
from decimal import Decimal

from app.domain.value_objects import Address, Coordinates, Money, PhoneNumber


def money(amount: Decimal | None) -> Money | None:
    """Build Money from Decimal, or None."""
    if amount is None:
        return None
    return Money(amount=amount)


def money_required(amount: Decimal) -> Money:
    """Build required Money from Decimal."""
    return Money(amount=amount)


def phone(number: str) -> PhoneNumber:
    """Build PhoneNumber from string."""
    return PhoneNumber(number=PhoneNumber.normalize(number))


def phone_optional(number: str | None) -> PhoneNumber | None:
    """Build optional PhoneNumber."""
    if number is None:
        return None
    return phone(number)


def address(
    *,
    street: str,
    ward: str,
    district: str,
    city: str,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Address:
    """Build Address value object."""
    return Address(
        street=street,
        ward=ward,
        district=district,
        city=city,
        latitude=latitude,
        longitude=longitude,
    )


def coordinates(latitude: float | None, longitude: float | None) -> Coordinates | None:
    """Build Coordinates when both values are present."""
    if latitude is None or longitude is None:
        return None
    return Coordinates(latitude=latitude, longitude=longitude)


def split_csv_uuids(value: str | None) -> list[uuid.UUID]:
    """Parse comma-separated UUID string."""
    if not value:
        return []
    return [uuid.UUID(part) for part in value.split(",") if part.strip()]


def join_csv_uuids(values: list[uuid.UUID]) -> str | None:
    """Serialize UUID list to CSV string."""
    if not values:
        return None
    return ",".join(str(v) for v in values)


def split_csv(value: str | None) -> list[str]:
    """Parse comma-separated string list."""
    if not value:
        return []
    return [part for part in value.split(",") if part.strip()]


def join_csv(values: list[str]) -> str | None:
    """Serialize string list to CSV."""
    if not values:
        return None
    return ",".join(values)


def dumps_json(data: dict[str, object] | None) -> str | None:
    """Serialize dict to JSON string."""
    if not data:
        return None
    return json.dumps(data)


def loads_json(value: str | None) -> dict[str, object]:
    """Deserialize JSON string to dict."""
    if not value:
        return {}
    loaded = json.loads(value)
    if isinstance(loaded, dict):
        return loaded
    return {}
