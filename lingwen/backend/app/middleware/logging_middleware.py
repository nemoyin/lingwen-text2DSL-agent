"""Request/response logging middleware."""

import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("lingwen.api")


class LoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that logs every HTTP request with method, path,
    status code, and elapsed time.
    """

    async def dispatch(self, request: Request, call_next):
        """Process an incoming request and log its details after the response.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler in the chain.

        Returns:
            The HTTP response produced by the downstream handler.
        """
        start_time = time.perf_counter()

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "%s %s %d %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        return response
