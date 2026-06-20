"""SQL execution node — runs the validated SQL against the user data source."""

import logging
import time
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.models.database import async_session
from app.services import datasource_service as ds_svc

logger = logging.getLogger(__name__)


class SQLExecutionNode:
    """Executes the validated SQL on the target data source.

    On success, records the result rows.  On failure, records the error
    so the pipeline can trigger a retry via the ``sql_generation`` node.
    """

    async def __call__(self, state: AgentState) -> Dict:
        """Execute the validated SQL.

        Args:
            state: Agent state with ``datasource_id`` and ``executed_sql``.

        Returns:
            ``{"execution_result": [...], "status": "success"}`` on success,
            or ``{"error_info": "...", "status": "failed"}`` on failure.
        """
        ds_id: int = state["datasource_id"]
        sql: str = state.get("executed_sql", "") or state.get("generated_sql", "")
        existing_error: str | None = state.get("error_info")
        t0 = time.time()

        if not sql:
            # Preserve any upstream error_info (e.g. from sql_validate)
            logger.warning("[Pipeline|SQL执行] 无可执行SQL, upstream_error=%s", existing_error)
            return {
                "error_info": existing_error or "无可执行的 SQL",
                "status": "failed",
            }

        logger.info("[Pipeline|SQL执行] 开始, ds_id=%d sql=%s", ds_id, sql[:150])

        async with async_session() as db:
            try:
                rows = await ds_svc.execute_query(db, ds_id, sql)
                elapsed = round((time.time() - t0) * 1000)
                logger.info("[Pipeline|SQL执行] 完成, rows=%d elapsed=%dms", len(rows), elapsed)
                return {
                    "execution_result": rows,
                    "status": "success",
                }
            except Exception as exc:
                error_str = str(exc)
                elapsed = round((time.time() - t0) * 1000)
                logger.error("[Pipeline|SQL执行] 失败, ds_id=%d error=%s elapsed=%dms",
                            ds_id, error_str[:100], elapsed)
                return {
                    "error_info": error_str,
                    "status": "failed",
                }
