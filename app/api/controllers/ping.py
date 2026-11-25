"""Ping controller for testing fastapi-controller integration."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

from fastapi_controller import controller

from app.api.controllers.base import BaseController

if TYPE_CHECKING:
    from fastapi_controller.controller_utils import ControllerBase as ControllerBaseType
else:
    ControllerBaseType = object

F = TypeVar("F", bound=Callable[..., Any])


def typed_get(path: str) -> Callable[[F], F]:
    """Typed wrapper for controller.get."""
    return cast(Callable[[F], F], controller.get(path))


class PingController(BaseController):  # type: ignore[misc]
    """Simple ping controller."""

    @typed_get("/")
    async def ping(self) -> dict[str, str]:
        """Ping endpoint."""
        return {"message": "pong"}

    @typed_get("/version")
    async def version(self) -> dict[str, str]:
        """Version endpoint."""
        return {"version": "0.1.0"}
