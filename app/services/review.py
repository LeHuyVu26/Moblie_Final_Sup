"""Review service."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Review as DomainReview
from app.domain.enums import OrderStatus
from app.repositories.order import OrderRepository
from app.repositories.review import ReviewRepository


class ReviewService:
    """Review service."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._review_repo = ReviewRepository(session)
        self._order_repo = OrderRepository(session)

    async def create_review(
        self,
        *,
        order_id: uuid.UUID,
        customer_id: uuid.UUID,
        rating: int,
        comment: str | None = None,
        images: list[str] | None = None,
    ) -> DomainReview:
        """Create a review for a delivered order."""
        existing = await self._review_repo.get_by_order(order_id)
        if existing:
            raise ValueError("Review already exists for this order")

        order = await self._order_repo.get(order_id)
        if not order:
            raise ValueError("Order not found")
        if order.customer_id != customer_id:
            raise ValueError("Order does not belong to this customer")
        if order.status != OrderStatus.DELIVERED:
            raise ValueError("Can only review delivered orders")

        review = DomainReview(
            order_id=order_id,
            customer_id=customer_id,
            restaurant_id=order.restaurant_id,
            rating=rating,
            comment=comment,
            images=images or [],
        )
        return await self._review_repo.add(review)

    async def get_restaurant_reviews(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainReview]:
        """Get reviews for a restaurant."""
        return await self._review_repo.get_by_restaurant(restaurant_id, limit=limit, offset=offset)

    async def get_order_review(self, order_id: uuid.UUID) -> DomainReview | None:
        """Get review for an order."""
        return await self._review_repo.get_by_order(order_id)
