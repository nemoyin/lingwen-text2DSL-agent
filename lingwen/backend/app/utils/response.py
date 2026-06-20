"""Helpers for building consistent API response dicts."""

from typing import Any, Optional


def success(
    data: Any = None,
    message: str = "success",
    code: int = 200,
) -> dict:
    """Build a success response dict conforming to ApiResponse schema.

    Args:
        data: The response payload.
        message: Human-readable message.
        code: HTTP status code (default 200).

    Returns:
        A dict with ``code``, ``data``, and ``message`` keys.
    """
    return {"code": code, "data": data, "message": message}


def error(
    code: int,
    message: str,
    detail: Optional[str] = None,
) -> dict:
    """Build an error response dict conforming to ErrorResponse schema.

    Args:
        code: Error code (see error code table in architecture doc).
        message: Human-readable error summary.
        detail: Optional additional detail string.

    Returns:
        A dict with ``code``, ``message``, ``detail``, and ``data`` (null) keys.
    """
    return {"code": code, "data": None, "message": message, "detail": detail}
