"""SQL validation node — security checks and LIMIT injection."""

import logging
import time
from typing import Dict

from app.agent.state import AgentState
from app.security.sql_guard import SqlGuard

logger = logging.getLogger(__name__)


class SQLValidationNode:
    """Validates generated SQL for safety and injects a row LIMIT.

    If validation fails, the error is recorded so the pipeline can retry.
    """

    def __init__(self, sql_guard: SqlGuard) -> None:
        """Args:
            sql_guard: An instance of :class:`SqlGuard`.
        """
        self._guard = sql_guard

    async def __call__(self, state: AgentState) -> Dict:
        """Validate the generated SQL.

        Args:
            state: Agent state with ``generated_sql``.

        Returns:
            ``{"executed_sql": ...}`` on success, or
            ``{"error_info": ...}`` on validation failure.
        """
        generated_sql: str = state.get("generated_sql", "")
        t0 = time.time()

        if not generated_sql:
            logger.error("[Pipeline|安全审计] SQL为空")
            return {"error_info": "生成的 SQL 为空"}

        logger.info("[Pipeline|安全审计] 开始验证, sql=%dchars", len(generated_sql))

        is_safe, error_msg = self._guard.validate(generated_sql)
        if not is_safe:
            elapsed = round((time.time() - t0) * 1000)
            logger.warning("[Pipeline|安全审计] 拒绝, reason=%s elapsed=%dms", error_msg, elapsed)
            return {"error_info": error_msg}

        safe_sql = self._guard.inject_limit(generated_sql)
        elapsed = round((time.time() - t0) * 1000)
        logger.info("[Pipeline|安全审计] 通过, injected_limit elapsed=%dms", elapsed)

        return {"executed_sql": safe_sql}
