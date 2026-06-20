"""Common Pydantic schemas used across all API routes."""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API success response envelope.

    All successful API responses use this format:
        {"code": 200, "data": {...}, "message": "success"}
    """

    code: int = Field(default=200, description="Status code; 200 for success")
    data: Optional[T] = Field(default=None, description="Response payload")
    message: str = Field(default="success", description="Human-readable message")


class ErrorResponse(BaseModel):
    """Standard API error response envelope.

    Error responses use this format:
        {"code": 40001, "message": "Error description", "detail": "..."}
    """

    code: int = Field(description="Error code (see error code table)")
    message: str = Field(description="Human-readable error message")
    detail: Optional[str] = Field(default=None, description="Optional error detail")


class PaginationParams(BaseModel):
    """Common pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page",
    )
