"""User repository implementation."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import User as DomainUser
from app.domain.enums import UserRole
from app.orm.models import User as UserModel
from app.repositories.base import BaseRepository
from app.repositories.mappers import phone


class UserRepository(BaseRepository[DomainUser, UserModel]):
    """User repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserModel)

    def _to_domain(self, model: UserModel) -> DomainUser:
        return DomainUser(
            id=model.id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            email=model.email,
            phone=phone(model.phone),
            full_name=model.full_name,
            password_hash=model.password_hash,
            role=model.role,
            is_active=model.is_active,
            avatar_url=model.avatar_url,
            last_login_at=model.last_login_at,
        )

    def _to_model(self, entity: DomainUser) -> UserModel:
        return UserModel(
            id=entity.id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            email=entity.email,
            phone=entity.phone.number,
            full_name=entity.full_name,
            password_hash=entity.password_hash,
            role=entity.role,
            is_active=entity.is_active,
            avatar_url=entity.avatar_url,
            last_login_at=entity.last_login_at,
        )

    async def get_by_email(self, email: str) -> DomainUser | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_phone(self, phone_number: str) -> DomainUser | None:
        stmt = select(UserModel).where(UserModel.phone == phone_number)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_role(self, role: UserRole, *, limit: int = 100, offset: int = 0) -> list[DomainUser]:
        stmt = select(UserModel).where(UserModel.role == role).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(model) for model in result.scalars().all()]
