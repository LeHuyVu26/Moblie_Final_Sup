"""Domain enums."""

from enum import Enum


class UserRole(str, Enum):
    """User roles in the system."""

    CUSTOMER = "CUSTOMER"
    OWNER = "OWNER"
    STAFF = "STAFF"


class OrderStatus(str, Enum):
    """Order lifecycle statuses."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY_FOR_PICKUP = "READY_FOR_PICKUP"
    DISPATCHED = "DISPATCHED"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class PaymentStatus(str, Enum):
    """Payment statuses."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class DeliveryProvider(str, Enum):
    """Supported delivery providers."""

    AHAMOVE = "AHAMOVE"
    LALAMOVE = "LALAMOVE"


class DeliveryStatus(str, Enum):
    """Delivery tracking statuses."""

    PENDING_DISPATCH = "PENDING_DISPATCH"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    DRIVER_EN_ROUTE_TO_PICKUP = "DRIVER_EN_ROUTE_TO_PICKUP"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PromotionType(str, Enum):
    """Promotion types."""

    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    FREE_DELIVERY = "FREE_DELIVERY"
    BUY_X_GET_Y = "BUY_X_GET_Y"


class MenuItemStatus(str, Enum):
    """Menu item availability statuses."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    HIDDEN = "HIDDEN"


class RestaurantStatus(str, Enum):
    """Restaurant operational statuses."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class PaymentMethod(str, Enum):
    """Supported payment methods."""

    CASH = "CASH"
    MOMO = "MOMO"
    ZALOPAY = "ZALOPAY"
    VNPAY = "VNPAY"
    CREDIT_CARD = "CREDIT_CARD"


class DiscountType(str, Enum):
    """Promotion discount types."""

    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    FREE_DELIVERY = "FREE_DELIVERY"


class PromotionStatus(str, Enum):
    """Promotion statuses."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
