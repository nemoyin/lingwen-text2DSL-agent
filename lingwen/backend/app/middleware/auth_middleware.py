"""Auth middleware — JWT token verification for protected routes."""

import logging
from typing import List

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.services.auth_service import verify_token

logger = logging.getLogger(__name__)

# Paths that do NOT require authentication
_WHITELIST_PATHS: List[str] = [
    "/api/auth/login",
    "/api/health",
    "/api/mcp",  # MCP Server — handles its own auth
    "/docs",
    "/openapi.json",
    "/redoc",
]


def _is_whitelisted(path: str) -> bool:
    """Check whether a request path is in the auth whitelist."""
    for wl in _WHITELIST_PATHS:
        if path.startswith(wl):
            return True
    return False


async def get_current_user(request: Request) -> dict:
    """Extract and verify the current user from the request's Authorization header.

    Designed to be used as a FastAPI dependency::

        @router.get("/protected")
        async def protected(user: dict = Depends(get_current_user)):
            ...

    Args:
        request: The incoming FastAPI request.

    Returns:
        A dict with ``user_id`` and ``username``.

    Raises:
        HTTPException(401): If the token is missing or invalid.
    """
    from app.api.deps import get_db as _get_db

    auth_header: str | None = request.headers.get("Authorization")
    if auth_header is None:
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证令牌格式错误")

    token: str = auth_header[7:]  # Strip "Bearer "
    if not token:
        raise HTTPException(status_code=401, detail="认证令牌为空")

    return verify_token(token)


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces JWT authentication on every request.

    Whitelisted paths (login, health, docs) are excluded from the check.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Check auth for non-whitelisted paths before passing to the route handler.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response.

        Raises:
            HTTPException(401): If authentication fails.
        """
        path: str = request.url.path

        # Allow OPTIONS (CORS preflight) through without auth
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip whitelisted paths
        if _is_whitelisted(path):
            return await call_next(request)

        auth_header: str | None = request.headers.get("Authorization")
        if auth_header is None or not auth_header.startswith("Bearer "):
            logger.warning("Missing or invalid auth header for %s %s", request.method, path)
            raise HTTPException(status_code=401, detail="未认证或令牌无效")

        token: str = auth_header[7:]
        if not token:
            raise HTTPException(status_code=401, detail="认证令牌为空")

        try:
            user_info = verify_token(token)
            # Inject user info into request state for downstream handlers
            request.state.user_id = user_info["user_id"]
            request.state.username = user_info["username"]
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Token verification error: %s", exc)
            raise HTTPException(status_code=401, detail="认证令牌无效")

        return await call_next(request)
