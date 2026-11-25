"""Order controller."""

from collections.abc import Callable
from typing import Any, TypeVar, cast
from uuid import UUID

from fastapi import HTTPException, status
from fastapi_controller import controller

from app.api.controllers.base import BaseController
from app.api.deps.auth import CurrentUser, DbSession
from app.api.deps.pagination import PaginationDep
from app.api.mappers import map_order, map_order_summary, map_page
from app.api.schemas.common import Page
from app.api.schemas.orders import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
    OrderSummaryResponse,
)
from app.domain.enums import PaymentStatus, UserRole
from app.repositories.payment import PaymentRepository
from app.repositories.restaurant import RestaurantRepository
from app.services.order import AddressInput, OrderItemInput, OrderService

F = TypeVar("F", bound=Callable[..., Any])


async def _order_response_context(session: DbSession, order: Any) -> tuple[str, PaymentStatus]:
    restaurant_repo = RestaurantRepository(session)
    payment_repo = PaymentRepository(session)
    restaurant = await restaurant_repo.get(order.restaurant_id)
    payment = await payment_repo.get_by_order(order.id)
    return (
        restaurant.name if restaurant else "",
        payment.status if payment else PaymentStatus.PENDING,
    )


def typed_get(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.get."""
    return cast(Callable[[F], F], controller.get(path))


def typed_post(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.post."""
    return cast(Callable[[F], F], controller.post(path))


def typed_patch(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.patch."""
    return cast(Callable[[F], F], controller.patch(path))


class OrderController(BaseController):  # type: ignore[misc]
    """Order endpoints."""

    @typed_post("/")
    async def create_order(self, request: OrderCreate, session: DbSession, current_user: CurrentUser) -> OrderResponse:
        """Create a new order."""
        service = OrderService(session)
        items: list[OrderItemInput] = [
            {
                "menu_item_id": item.menu_item_id,
                "quantity": item.quantity,
                "special_instructions": item.special_instructions,
            }
            for item in request.items
        ]
        address: AddressInput = {
            "street": request.delivery_address.street,
            "ward": request.delivery_address.ward,
            "district": request.delivery_address.district,
            "city": request.delivery_address.city,
            "latitude": (
                float(request.delivery_address.latitude) if request.delivery_address.latitude is not None else None
            ),
            "longitude": (
                float(request.delivery_address.longitude) if request.delivery_address.longitude is not None else None
            ),
        }
        try:
            order = await service.create_order(
                customer_id=current_user.id,
                restaurant_id=request.restaurant_id,
                items=items,
                delivery_address=address,
                promotion_code=request.promotion_code,
                notes=request.notes,
                scheduled_for=request.scheduled_for,
            )
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        restaurant_name, payment_status = await _order_response_context(session, order)
        return map_order(order, restaurant_name=restaurant_name, payment_status=payment_status)

    @typed_get("/{order_id}")
    async def get_order(self, order_id: UUID, session: DbSession, current_user: CurrentUser) -> OrderResponse:
        """Get order by ID."""
        service = OrderService(session)
        order = await service.get_order(order_id)
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        if order.customer_id != current_user.id and current_user.role != UserRole.STAFF:
            restaurant = await RestaurantRepository(session).get(order.restaurant_id)
            owns_restaurant = (
                current_user.role == UserRole.OWNER and restaurant is not None and restaurant.owner_id == current_user.id
            )
            if not owns_restaurant:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        restaurant_name, payment_status = await _order_response_context(session, order)
        return map_order(order, restaurant_name=restaurant_name, payment_status=payment_status)

    @typed_get("/")
    async def list_orders(
        self, session: DbSession, current_user: CurrentUser, pagination: PaginationDep
    ) -> Page[OrderSummaryResponse]:
        """List orders for current user."""
        service = OrderService(session)
        if current_user.role == UserRole.STAFF:
            orders = await service.list_all_orders(limit=pagination.limit, offset=pagination.offset)
        elif current_user.role == UserRole.OWNER:
            shops = await RestaurantRepository(session).get_by_owner(current_user.id)
            orders = []
            for shop in shops:
                orders.extend(
                    await service.get_restaurant_orders(shop.id, limit=pagination.limit, offset=pagination.offset)
                )
            orders.sort(key=lambda o: o.created_at, reverse=True)
        else:
            orders = await service.get_customer_orders(
                current_user.id, limit=pagination.limit, offset=pagination.offset
            )
        mapped: list[OrderSummaryResponse] = []
        for order in orders:
            restaurant_name, payment_status = await _order_response_context(session, order)
            mapped.append(map_order_summary(order, restaurant_name=restaurant_name, payment_status=payment_status))
        return map_page(mapped, total=len(orders), page=pagination.page, size=pagination.limit)

    @typed_patch("/{order_id}/status")
    async def update_order_status(
        self,
        order_id: UUID,
        request: OrderStatusUpdate,
        session: DbSession,
        current_user: CurrentUser,
    ) -> OrderResponse:
        """Update order status (restaurant/staff only)."""
        if current_user.role not in (UserRole.OWNER, UserRole.STAFF):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        service = OrderService(session)
        try:
            order = await service.update_order_status(order_id, request.status, request.reason)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        restaurant_name, payment_status = await _order_response_context(session, order)
        return map_order(order, restaurant_name=restaurant_name, payment_status=payment_status)

    @typed_post("/{order_id}/reorder")
    async def reorder(self, order_id: UUID, session: DbSession, current_user: CurrentUser) -> OrderResponse:
        """Reorder a previous delivered order."""
        service = OrderService(session)
        try:
            order = await service.reorder(order_id, current_user.id)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        restaurant_name, payment_status = await _order_response_context(session, order)
        return map_order(order, restaurant_name=restaurant_name, payment_status=payment_status)