"""Base controller for fastapi-controller integration."""

from fastapi_controller import create_controller

# Create base controller class with version prefix
BaseController = create_controller("/v{version}/{controller}", "1")
