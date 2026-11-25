"""Base classes for domain models using Pydantic v2."""

from __future__ import annotations

import uuid
from abc import ABC
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class StrictModel(BaseModel):
    """Base model with strict configuration."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True,
        alias_generator=to_camel,
        frozen=False,
    )


class FrozenStrictModel(BaseModel):
    """Base model with strict configuration and frozen=True."""

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True,
        alias_generator=to_camel,
        frozen=True,
    )


class DomainEntity(StrictModel, ABC):
    """Base class for domain entities with identity."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()


class ValueObject(FrozenStrictModel, ABC):
    """Base class for immutable value objects."""

    pass


class DomainEvent(StrictModel, ABC):
    """Base class for domain events."""

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    event_type: str = Field(default="")

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.event_type:
            cls.event_type = cls.__name__


T = TypeVar("T", bound=DomainEntity)


class Repository(Generic[T], ABC):
    """Abstract base repository."""

    async def add(self, entity: T) -> T:
        raise NotImplementedError

    async def get(self, entity_id: uuid.UUID) -> T | None:
        raise NotImplementedError

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[T]:
        raise NotImplementedError

    async def remove(self, entity_id: uuid.UUID) -> bool:
        raise NotImplementedError
