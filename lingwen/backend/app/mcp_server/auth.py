"""MCP Server JWT authentication."""
import logging
from app.services.auth_service import verify_token

logger = logging.getLogger(__name__)


class MCPAuth:
    """Validates JWT tokens for MCP tool calls.

    The token is passed via MCP initialization parameters or environment.
    Tokens are validated against the same JWT secret used by the main API.
    """

    def __init__(self):
        self._users: dict[str, dict] = {}  # token -> user_info cache

    def authenticate(self, token: str | None) -> dict:
        """Verify JWT token and return user info.

        Returns a dict with user_id and username.
        Raises ValueError if the token is missing or invalid.
        """
        if not token:
            raise ValueError("MCP authentication required — set LINGWEN_JWT_TOKEN env var")

        if token in self._users:
            return self._users[token]

        try:
            user = verify_token(token)
            self._users[token] = user
            return user
        except Exception as e:
            logger.warning("MCP auth failed: %s", e)
            raise ValueError(f"Invalid JWT token: {e}") from e
