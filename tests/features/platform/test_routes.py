"""Route inventory checks after namespace-package conversion."""

from __future__ import annotations

from fastapi import FastAPI

from app.main import app
from tests.helpers import route_inventory

EXPECTED_ROUTES = {
    ("GET", "/health"),
    ("GET", "/health/ready"),
    ("GET", "/v1/ping/"),
    ("GET", "/v1/ping/version"),
    ("POST", "/v1/auth/register"),
    ("POST", "/v1/auth/login"),
    ("POST", "/v1/auth/refresh"),
    ("GET", "/v1/auth/me"),
    ("GET", "/v1/user/"),
    ("GET", "/v1/user/{user_id}"),
    ("POST", "/v1/user/"),
    ("PATCH", "/v1/user/{user_id}"),
    ("POST", "/v1/user/{user_id}/change-password"),
    ("GET", "/v1/restaurant/"),
    ("GET", "/v1/restaurant/{restaurant_id}"),
    ("POST", "/v1/restaurant/"),
    ("PATCH", "/v1/restaurant/{restaurant_id}"),
    ("DELETE", "/v1/restaurant/{restaurant_id}"),
    ("GET", "/v1/menu/{restaurant_id}/categories"),
    ("POST", "/v1/menu/{restaurant_id}/categories"),
    ("PATCH", "/v1/menu/categories/{category_id}"),
    ("DELETE", "/v1/menu/categories/{category_id}"),
    ("GET", "/v1/menu/{restaurant_id}/items"),
    ("POST", "/v1/menu/{restaurant_id}/items"),
    ("PATCH", "/v1/menu/items/{item_id}"),
    ("DELETE", "/v1/menu/items/{item_id}"),
    ("GET", "/v1/menu/{restaurant_id}/promotions"),
    ("POST", "/v1/menu/{restaurant_id}/promotions"),
    ("PATCH", "/v1/menu/promotions/{promotion_id}"),
    ("DELETE", "/v1/menu/promotions/{promotion_id}"),
    ("POST", "/v1/order/"),
    ("GET", "/v1/order/"),
    ("GET", "/v1/order/{order_id}"),
    ("PATCH", "/v1/order/{order_id}/status"),
    ("POST", "/v1/order/{order_id}/reorder"),
    ("POST", "/v1/payment/{order_id}/payments"),
    ("GET", "/v1/payment/{order_id}/payments"),
    ("POST", "/v1/payment/payments/{payment_id}/confirm"),
    ("POST", "/v1/payment/payments/{payment_id}/refund"),
    ("GET", "/v1/delivery/{order_id}/delivery"),
    ("POST", "/v1/delivery/{order_id}/delivery/dispatch"),
    ("PATCH", "/v1/delivery/{order_id}/delivery/tracking"),
    ("POST", "/v1/review/{order_id}/reviews"),
    ("GET", "/v1/review/restaurants/{restaurant_id}/reviews"),
}


def test_all_expected_routes_are_registered() -> None:
    assert route_inventory(app) >= EXPECTED_ROUTES


def test_docs_routes_are_enabled() -> None:
    routes = route_inventory(app)
    assert ("GET", "/docs") in routes
    assert ("GET", "/redoc") in routes
    assert ("GET", "/openapi.json") in routes


def test_docs_routes_are_independent_of_debug() -> None:
    import os

    from app.config.settings import get_settings
    from app.main import create_app

    os.environ["DEBUG"] = "false"
    get_settings.cache_clear()
    try:
        new_app = create_app()
        new_routes = route_inventory(new_app)
        assert ("GET", "/docs") in new_routes
        assert ("GET", "/redoc") in new_routes
        assert ("GET", "/openapi.json") in new_routes
    finally:
        get_settings.cache_clear()
        os.environ.pop("DEBUG", None)


def test_create_app_returns_independent_app() -> None:
    from app.main import create_app

    other: FastAPI = create_app()
    assert other is not app
    assert EXPECTED_ROUTES - {("GET", "/health"), ("GET", "/health/ready")} <= route_inventory(other)
