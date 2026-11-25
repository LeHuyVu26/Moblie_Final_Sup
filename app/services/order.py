"""Order service."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Order as DomainOrder
from app.domain.entities import OrderItem as DomainOrderItem
from app.domain.enums import OrderStatus, PromotionType
from app.domain.value_objects import Address, Money
from app.repositories.menu_item import MenuItemRepository
from app.repositories.order import OrderRepository
from app.repositories.promotion import PromotionRepository
from app.repositories.restaurant import RestaurantRepository
from app.services.delivery import DeliveryService


class OrderItemInput(TypedDict):
    """Input for an order item."""

    menu_item_id: uuid.UUID
    quantity: int
    special_instructions: str | None


class AddressInput(TypedDict):
    """Input for a delivery address."""

    street: str
    ward: str
    district: str
    city: str
    latitude: float | None
    longitude: float | None


class OrderService:
    """Order service for order management."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._order_repo = OrderRepository(session)
        self._menu_item_repo = MenuItemRepository(session)
        self._promotion_repo = PromotionRepository(session)
        self._restaurant_repo = RestaurantRepository(session)
        self._delivery_service = DeliveryService(session)

    async def create_order(  # noqa: PLR0912
        self,
        *,
        customer_id: uuid.UUID,
        restaurant_id: uuid.UUID,
        items: list[OrderItemInput],
        delivery_address: AddressInput,
        promotion_code: str | None = None,
        notes: str | None = None,
        scheduled_for: datetime | None = None,
    ) -> DomainOrder:
        """Create a new order with items and calculate totals."""
        # Verify restaurant exists and is active
        restaurant = await self._restaurant_repo.get(restaurant_id)
        if not restaurant:
            raise ValueError("Restaurant not found")
        if not restaurant.is_active:
            raise ValueError("Restaurant is not active")

        # Verify menu items exist and are available
        order_items: list[DomainOrderItem] = []
        subtotal = Decimal("0")

        for item_data in items:
            menu_item = await self._menu_item_repo.get(item_data["menu_item_id"])
            if not menu_item:
                raise ValueError(f"Menu item {item_data['menu_item_id']} not found")
            if str(menu_item.status) != "AVAILABLE":
                raise ValueError(f"Menu item {menu_item.name} is not available")

            quantity = item_data["quantity"]
            special_instructions = item_data.get("special_instructions")

            order_item = DomainOrderItem.create(
                order_id=uuid.uuid4(),  # temporary, will be set after order creation
                menu_item_id=menu_item.id,
                menu_item_name=menu_item.name,
                menu_item_price=menu_item.price,
                quantity=quantity,
                note=special_instructions,
            )
            order_items.append(order_item)
            subtotal += order_item.subtotal.amount

        # Calculate delivery fee
        delivery_fee = restaurant.delivery_fee.amount

        # Apply promotion if provided
        discount_amount = Decimal("0")
        promotion_id = None
        if promotion_code:
            promotions = await self._promotion_repo.get_active_by_restaurant(restaurant_id)
            promo = next((p for p in promotions if p.name == promotion_code), None)
            if promo and promo.is_valid():
                if promo.min_order_amount and subtotal < promo.min_order_amount.amount:
                    raise ValueError(f"Minimum order amount for this promotion is {promo.min_order_amount}")
                if promo.type == PromotionType.PERCENTAGE:
                    discount_amount = subtotal * (promo.value / Decimal("100"))
                    if promo.max_discount_amount:
                        discount_amount = min(discount_amount, promo.max_discount_amount.amount)
                elif promo.type == PromotionType.FIXED_AMOUNT:
                    discount_amount = min(promo.value, subtotal)
                elif promo.type == PromotionType.FREE_DELIVERY:
                    discount_amount = delivery_fee
                promotion_id = promo.id

        # Ensure discount doesn't exceed subtotal
        discount_amount = min(discount_amount, subtotal)

        total_amount = subtotal + delivery_fee - discount_amount

        # Create order
        order = DomainOrder(
            customer_id=customer_id,
            restaurant_id=restaurant_id,
            items=order_items,
            subtotal=Money(amount=subtotal),
            delivery_fee=Money(amount=delivery_fee),
            discount_amount=Money(amount=discount_amount),
            total_amount=Money(amount=total_amount),
            promotion_id=promotion_id,
            promotion_code=promotion_code,
            delivery_address=Address(**delivery_address),
            customer_note=notes,
        )

        # Set order_id on items
        for item in order.items:
            item.order_id = order.id

        # Save order
        saved_order = await self._order_repo.add(order)

        # Update promotion usage count if used
        if promotion_id:
            promo = await self._promotion_repo.get(promotion_id)
            if promo:
                promo.usage_count += 1
                await self._promotion_repo.update(promo)

        return saved_order

    async def get_order(self, order_id: uuid.UUID) -> DomainOrder | None:
        """Get order by ID."""
        return await self._order_repo.get(order_id)

    async def get_customer_orders(
        self, customer_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainOrder]:
        """Get orders for a customer."""
        return await self._order_repo.get_by_customer(customer_id, limit=limit, offset=offset)

    async def get_restaurant_orders(
        self, restaurant_id: uuid.UUID, *, limit: int = 100, offset: int = 0
    ) -> list[DomainOrder]:
        """Get orders for a restaurant."""
        return await self._order_repo.get_by_restaurant(restaurant_id, limit=limit, offset=offset)

    async def get_orders_by_status(
        self, status: OrderStatus, *, limit: int = 100, offset: int = 0
    ) -> list[DomainOrder]:
        """Get orders by status."""
        return await self._order_repo.get_by_status(status, limit=limit, offset=offset)

    async def list_all_orders(self, *, limit: int = 100, offset: int = 0) -> list[DomainOrder]:
        """List all orders (staff use)."""
        return await self._order_repo.list_all(limit=limit, offset=offset)

    async def update_order_status(
        self, order_id: uuid.UUID, new_status: OrderStatus, reason: str | None = None
    ) -> DomainOrder:
        """Update order status."""
        order = await self._order_repo.get(order_id)
        if not order:
            raise ValueError("Order not found")

        if not order.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {order.status} to {new_status}")

        order.transition_to(new_status)
        if new_status == OrderStatus.CANCELLED and reason:
            order.cancellation_reason = reason

        updated_order = await self._order_repo.update(order)

        # If order is ready for pickup, auto-dispatch delivery
        if new_status == OrderStatus.READY_FOR_PICKUP:
            await self._delivery_service.auto_dispatch(order_id)

        return updated_order

    async def cancel_order(self, order_id: uuid.UUID, reason: str) -> DomainOrder:
        """Cancel an order."""
        return await self.update_order_status(order_id, OrderStatus.CANCELLED, reason)

    async def reorder(self, order_id: uuid.UUID, customer_id: uuid.UUID) -> DomainOrder:
        """Create a new order based on a previous order."""
        original_order = await self._order_repo.get(order_id)
        if not original_order:
            raise ValueError("Original order not found")
        if original_order.customer_id != customer_id:
            raise ValueError("Order does not belong to this customer")
        if original_order.status != OrderStatus.DELIVERED:
            raise ValueError("Can only reorder delivered orders")

        items: list[OrderItemInput] = [
            {
                "menu_item_id": item.menu_item_id,
                "quantity": item.quantity,
                "special_instructions": item.note,
            }
            for item in original_order.items
        ]

        return await self.create_order(
            customer_id=customer_id,
            restaurant_id=original_order.restaurant_id,
            items=items,
            delivery_address={
                "street": original_order.delivery_address.street,
                "ward": original_order.delivery_address.ward,
                "district": original_order.delivery_address.district,
                "city": original_order.delivery_address.city,
                "latitude": original_order.delivery_address.latitude,
                "longitude": original_order.delivery_address.longitude,
            },
            notes=original_order.customer_note,
        )
