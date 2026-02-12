"""Shared Pydantic base models."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    model_config = ConfigDict(from_attributes=True)


class TimestampMixin(BaseModel):
    """Mixin for created_at / updated_at fields."""
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Standard paginated response wrapper."""
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


class HealthResponse(BaseModel):
    """Standard health check response."""
    status: str = "healthy"
    service: str
    version: str = "0.1.0"


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    error_code: Optional[str] = None
