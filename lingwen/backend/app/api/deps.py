"""Dependency injection helpers for FastAPI routes."""

import logging
import os
from typing import AsyncGenerator, Optional

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import get_db as _get_db

logger = logging.getLogger(__name__)

# Singleton QueryAgent — created on first access
_agent_instance = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session."""
    async for session in _get_db():
        yield session


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    """Validate JWT token and return the current user."""
    if authorization is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    from app.services.auth_service import verify_token
    return verify_token(token)


def _load_model_config_sync() -> Optional[dict]:
    """Load the default model config using a sync pymysql connection.

    Called once during agent initialisation — does NOT use the async session.
    """
    import pymysql
    from app.config import settings as s

    try:
        conn = pymysql.connect(
            host=s.db_host, port=s.db_port, user=s.db_user, password=s.db_password,
            database=s.db_name, charset="utf8mb4",
        )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM model_configs WHERE is_active=1 AND is_default=1 LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                cur.execute(
                    "SELECT * FROM model_configs WHERE is_active=1 ORDER BY id LIMIT 1"
                )
                row = cur.fetchone()
            if row:
                cols = [d[0] for d in cur.description]
                return dict(zip(cols, row))
        conn.close()
        return None
    except Exception as exc:
        logger.warning("Failed to load model config: %s", exc)
        return None


async def get_agent():
    """Return the shared QueryAgent singleton instance.

    On first call, fetches the active default model from the model_configs
    table and builds the appropriate LLM.  Subsequent calls return the cached
    singleton (restart required to pick up model changes).
    """
    global _agent_instance

    if _agent_instance is None:
        from app.agent.graph import QueryAgent
        from app.services.model_service import build_llm

        logger.info("Initialising QueryAgent singleton — loading default model ...")
        model_config = _load_model_config_sync()
        if model_config:
            logger.info("Using model: %s [%s]", model_config.get("name"), model_config.get("provider"))
            llm = build_llm(model_config)
        else:
            logger.warning("No model configured in model_configs — using settings fallback")
            llm = None  # QueryAgent.__init__ will fall back to settings

        _agent_instance = QueryAgent(llm=llm)
        logger.info("QueryAgent singleton ready")

    return _agent_instance
