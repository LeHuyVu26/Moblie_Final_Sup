"""Pagination dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query

from app.config.settings import get_settings


@dataclass(frozen=True, slots=True)
class Pagination:
    """Pagination parameters."""

    limit: int
    offset: int

    @property
    def page(self) -> int:
        """1-based page number."""
        return self.offset // self.limit + 1


def pagination_params(
    page: Annotated[int, Query(ge=1, description="1-based page number")] = 1,
    size: Annotated[int, Query(ge=1, description="Items per page")] = 20,
) -> Pagination:
    """Build pagination parameters from query string."""
    settings = get_settings()
    limit = min(size, settings.max_page_size)
    return Pagination(limit=limit, offset=(page - 1) * limit)


PaginationDep = Annotated[Pagination, Depends(pagination_params)]
