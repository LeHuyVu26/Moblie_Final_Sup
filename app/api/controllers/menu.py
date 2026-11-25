"""Menu controller (categories, menu items, promotions)."""

from collections.abc import Callable
from datetime import datetime, time
from typing import Any, TypeVar, cast
from uuid import UUID

from fastapi import HTTPException, status
from fastapi_controller import controller

from app.api.controllers.base import BaseController
from app.api.deps.auth import CurrentUser, DbSession
from app.api.deps.pagination import PaginationDep
from app.api.mappers import map_category, map_menu_item, map_page, map_promotion
from app.api.schemas.categories import CategoryCreate, CategoryResponse, CategoryUpdate
from app.api.schemas.common import Page
from app.api.schemas.menu_items import MenuItemCreate, MenuItemResponse, MenuItemUpdate
from app.api.schemas.promotions import PromotionCreate, PromotionResponse, PromotionUpdate
from app.domain.entities import Category as DomainCategory
from app.domain.entities import MenuItem as DomainMenuItem
from app.domain.entities import Promotion as DomainPromotion
from app.domain.enums import PromotionStatus, PromotionType, UserRole
from app.domain.value_objects import Money
from app.repositories.category import CategoryRepository
from app.repositories.menu_item import MenuItemRepository
from app.repositories.promotion import PromotionRepository
from app.repositories.restaurant import RestaurantRepository

F = TypeVar("F", bound=Callable[..., Any])


def typed_get(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.get."""
    return cast(Callable[[F], F], controller.get(path))


def typed_post(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.post."""
    return cast(Callable[[F], F], controller.post(path))


def typed_patch(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.patch."""
    return cast(Callable[[F], F], controller.patch(path))


def typed_delete(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.delete."""
    return cast(Callable[[F], F], controller.delete(path))


async def _ensure_restaurant_owner(session: DbSession, restaurant_id: UUID, current_user: Any) -> None:
    """Ensure current user owns the restaurant."""
    repo = RestaurantRepository(session)
    restaurant = await repo.get(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found")
    if restaurant.owner_id != current_user.id and current_user.role != UserRole.STAFF:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")


class MenuController(BaseController):  # type: ignore[misc]
    """Menu management endpoints."""

    # Categories
    @typed_get("/{restaurant_id}/categories")
    async def list_categories(
        self, restaurant_id: UUID, session: DbSession, pagination: PaginationDep
    ) -> Page[CategoryResponse]:
        """List categories for a restaurant."""
        repo = CategoryRepository(session)
        categories = await repo.get_by_restaurant(restaurant_id, limit=pagination.limit, offset=pagination.offset)
        return map_page(
            [map_category(c) for c in categories],
            total=len(categories),
            page=pagination.page,
            size=pagination.limit,
        )

    @typed_post("/{restaurant_id}/categories")
    async def create_category(
        self, restaurant_id: UUID, request: CategoryCreate, session: DbSession, current_user: CurrentUser
    ) -> CategoryResponse:
        """Create a category."""
        await _ensure_restaurant_owner(session, restaurant_id, current_user)
        repo = CategoryRepository(session)
        category = DomainCategory(
            restaurant_id=restaurant_id,
            name=request.name,
            description=request.description,
            display_order=request.display_order,
        )
        saved = await repo.add(category)
        return map_category(saved)

    @typed_patch("/categories/{category_id}")
    async def update_category(
        self, category_id: UUID, request: CategoryUpdate, session: DbSession, current_user: CurrentUser
    ) -> CategoryResponse:
        """Update a category."""
        repo = CategoryRepository(session)
        category = await repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await _ensure_restaurant_owner(session, category.restaurant_id, current_user)
        for field, value in request.model_dump(exclude_unset=True).items():
            if hasattr(category, field):
                setattr(category, field, value)
        category.touch()
        saved = await repo.update(category)
        return map_category(saved)

    @typed_delete("/categories/{category_id}")
    async def delete_category(self, category_id: UUID, session: DbSession, current_user: CurrentUser) -> dict[str, str]:
        """Delete a category."""
        repo = CategoryRepository(session)
        category = await repo.get(category_id)
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        await _ensure_restaurant_owner(session, category.restaurant_id, current_user)
        await repo.remove(category_id)
        return {"message": "Category deleted"}

    # Menu items
    @typed_get("/{restaurant_id}/items")
    async def list_menu_items(
        self, restaurant_id: UUID, session: DbSession, pagination: PaginationDep
    ) -> Page[MenuItemResponse]:
        """List menu items for a restaurant."""
        repo = MenuItemRepository(session)
        items = await repo.get_by_restaurant(restaurant_id, limit=pagination.limit, offset=pagination.offset)
        return map_page(
            [map_menu_item(i) for i in items],
            total=len(items),
            page=pagination.page,
            size=pagination.limit,
        )

    @typed_post("/{restaurant_id}/items")
    async def create_menu_item(
        self, restaurant_id: UUID, request: MenuItemCreate, session: DbSession, current_user: CurrentUser
    ) -> MenuItemResponse:
        """Create a menu item."""
        await _ensure_restaurant_owner(session, restaurant_id, current_user)
        repo = MenuItemRepository(session)
        item = DomainMenuItem(
            restaurant_id=restaurant_id,
            category_id=request.category_id,
            name=request.name,
            description=request.description,
            price=Money(amount=request.price),
            original_price=Money(amount=request.discounted_price) if request.discounted_price else None,
            image_url=request.image_url,
            status=request.status,
            is_vegetarian=False,
            is_vegan=False,
            is_spicy=False,
            preparation_time_minutes=request.preparation_time_minutes,
            allergens=request.allergens,
        )
        saved = await repo.add(item)
        return map_menu_item(saved)

    @typed_patch("/items/{item_id}")
    async def update_menu_item(
        self, item_id: UUID, request: MenuItemUpdate, session: DbSession, current_user: CurrentUser
    ) -> MenuItemResponse:
        """Update a menu item."""
        repo = MenuItemRepository(session)
        item = await repo.get(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        await _ensure_restaurant_owner(session, item.restaurant_id, current_user)
        data = request.model_dump(exclude_unset=True)
        if "price" in data and data["price"] is not None:
            item.price = Money(amount=data["price"])
            del data["price"]
        if "discounted_price" in data:
            item.original_price = Money(amount=data["discounted_price"]) if data["discounted_price"] else None
            del data["discounted_price"]
        for field, value in data.items():
            if hasattr(item, field):
                setattr(item, field, value)
        item.touch()
        saved = await repo.update(item)
        return map_menu_item(saved)

    @typed_delete("/items/{item_id}")
    async def delete_menu_item(self, item_id: UUID, session: DbSession, current_user: CurrentUser) -> dict[str, str]:
        """Delete a menu item."""
        repo = MenuItemRepository(session)
        item = await repo.get(item_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Menu item not found")
        await _ensure_restaurant_owner(session, item.restaurant_id, current_user)
        await repo.remove(item_id)
        return {"message": "Menu item deleted"}

    # Promotions
    @typed_get("/{restaurant_id}/promotions")
    async def list_promotions(
        self, restaurant_id: UUID, session: DbSession, pagination: PaginationDep
    ) -> Page[PromotionResponse]:
        """List promotions for a restaurant."""
        repo = PromotionRepository(session)
        promotions = await repo.get_by_restaurant(restaurant_id, limit=pagination.limit, offset=pagination.offset)
        return map_page(
            [map_promotion(p) for p in promotions],
            total=len(promotions),
            page=pagination.page,
            size=pagination.limit,
        )

    @typed_post("/{restaurant_id}/promotions")
    async def create_promotion(
        self, restaurant_id: UUID, request: PromotionCreate, session: DbSession, current_user: CurrentUser
    ) -> PromotionResponse:
        """Create a promotion."""
        await _ensure_restaurant_owner(session, restaurant_id, current_user)
        repo = PromotionRepository(session)
        promotion = DomainPromotion(
            restaurant_id=restaurant_id,
            name=request.code,
            description=request.description,
            type=PromotionType(request.discount_type),
            value=request.discount_value,
            min_order_amount=Money(amount=request.minimum_order_amount),
            max_discount_amount=(
                Money(amount=request.maximum_discount_amount) if request.maximum_discount_amount else None
            ),
            usage_limit=request.usage_limit,
            start_at=datetime.combine(request.start_date, time.min),
            end_at=datetime.combine(request.end_date, time.max),
            is_active=request.status == PromotionStatus.ACTIVE,
            applicable_menu_item_ids=request.applicable_item_ids,
            applicable_category_ids=request.applicable_category_ids,
        )
        saved = await repo.add(promotion)
        return map_promotion(saved)

    @typed_patch("/promotions/{promotion_id}")
    async def update_promotion(
        self, promotion_id: UUID, request: PromotionUpdate, session: DbSession, current_user: CurrentUser
    ) -> PromotionResponse:
        """Update a promotion."""
        repo = PromotionRepository(session)
        promotion = await repo.get(promotion_id)
        if not promotion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
        await _ensure_restaurant_owner(session, promotion.restaurant_id, current_user)
        data = request.model_dump(exclude_unset=True)
        if "code" in data and data["code"] is not None:
            promotion.name = data["code"]
            del data["code"]
        for field, value in data.items():
            if hasattr(promotion, field):
                setattr(promotion, field, value)
        promotion.touch()
        saved = await repo.update(promotion)
        return map_promotion(saved)

    @typed_delete("/promotions/{promotion_id}")
    async def delete_promotion(
        self, promotion_id: UUID, session: DbSession, current_user: CurrentUser
    ) -> dict[str, str]:
        """Delete a promotion."""
        repo = PromotionRepository(session)
        promotion = await repo.get(promotion_id)
        if not promotion:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promotion not found")
        await _ensure_restaurant_owner(session, promotion.restaurant_id, current_user)
        await repo.remove(promotion_id)
        return {"message": "Promotion deleted"}
