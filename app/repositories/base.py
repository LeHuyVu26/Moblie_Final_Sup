"""Base repository implementation."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.base import DomainEntity, Repository
from app.orm.base import Base

T = TypeVar("T", bound=DomainEntity)
M = TypeVar("M", bound=Base)


class BaseRepository(Repository[T], Generic[T, M], ABC):
    """Base repository with common CRUD operations."""

    def __init__(self, session: AsyncSession, model: type[M]) -> None:
        self._session = session
        self._model = model

    @abstractmethod
    def _to_domain(self, model: M) -> T:
        """Convert ORM model to domain entity."""

    @abstractmethod
    def _to_model(self, entity: T) -> M:
        """Convert domain entity to ORM model."""

    async def add(self, entity: T) -> T:
        """Add entity to database."""
        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def get(self, entity_id: uuid.UUID) -> T | None:
        """Get entity by ID."""
        stmt = select(self._model).where(self._model.id == entity_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[T]:
        """List entities with pagination."""
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        stmt = select(self._model).where(self._model.id == entity.id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            raise ValueError(f"Entity {entity.id} not found")
        updated = self._to_model(entity)
        for column in model.__table__.columns:
            setattr(model, column.name, getattr(updated, column.name))
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def remove(self, entity_id: uuid.UUID) -> bool:
        """Remove entity by ID."""
        stmt = select(self._model).where(self._model.id == entity_id)  # type: ignore[attr-defined]
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return False
        await self._session.delete(model)
        await self._session.flush()
        return True
