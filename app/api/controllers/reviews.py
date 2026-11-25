"""Review controller."""

from collections.abc import Callable
from typing import Any, TypeVar, cast
from uuid import UUID

from fastapi import HTTPException, status
from fastapi_controller import controller

from app.api.controllers.base import BaseController
from app.api.deps.auth import CurrentUser, DbSession
from app.api.deps.pagination import PaginationDep
from app.api.mappers import map_page, map_review
from app.api.schemas.common import Page
from app.api.schemas.reviews import ReviewCreate, ReviewResponse
from app.services.review import ReviewService

F = TypeVar("F", bound=Callable[..., Any])


def typed_get(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.get."""
    return cast(Callable[[F], F], controller.get(path))


def typed_post(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.post."""
    return cast(Callable[[F], F], controller.post(path))


class ReviewController(BaseController):  # type: ignore[misc]
    """Review endpoints."""

    @typed_post("/{order_id}/reviews")
    async def create_review(
        self, order_id: UUID, request: ReviewCreate, session: DbSession, current_user: CurrentUser
    ) -> ReviewResponse:
        """Create a review for a delivered order."""
        service = ReviewService(session)
        try:
            review = await service.create_review(
                order_id=order_id,
                customer_id=current_user.id,
                rating=request.rating,
                comment=request.comment,
                images=request.images,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        return map_review(review)

    @typed_get("/restaurants/{restaurant_id}/reviews")
    async def list_reviews(
        self, restaurant_id: UUID, session: DbSession, pagination: PaginationDep
    ) -> Page[ReviewResponse]:
        """List reviews for a restaurant."""
        service = ReviewService(session)
        reviews = await service.get_restaurant_reviews(restaurant_id, limit=pagination.limit, offset=pagination.offset)
        return map_page(
            [map_review(r) for r in reviews],
            total=len(reviews),
            page=pagination.page,
            size=pagination.limit,
        )
