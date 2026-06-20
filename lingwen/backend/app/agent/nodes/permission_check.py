"""Permission check node — validates that the target data source is active."""

import logging
import time
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.models.database import async_session
from app.services import datasource_service as ds_svc

logger = logging.getLogger(__name__)


class PermissionCheckNode:
    """Ensures the requested data source exists and is in ``active`` status."""

    async def __call__(self, state: AgentState) -> Dict:
        """Check data source availability.

        Args:
            state: The current agent state with ``datasource_id`` set.

        Returns:
            ``{"status": "init"}`` when the source is usable, or
            ``{"status": "auth_failed", "error_info": "..."}`` otherwise.
        """
        ds_id: int = state["datasource_id"]
        t0 = time.time()
        logger.info("[Pipeline|权限校验] 开始验证, datasource_id=%d", ds_id)

        async with async_session() as db:
            try:
                ds = await ds_svc.get(db, ds_id)
            except Exception as exc:
                elapsed = round((time.time() - t0) * 1000)
                logger.error("[Pipeline|权限校验] 数据源不存在 ds_id=%d elapsed=%dms error=%s", ds_id, elapsed, exc)
                return {
                    "status": "auth_failed",
                    "error_info": f"数据源不存在 (id={ds_id})",
                }

            if ds.status != "active":
                elapsed = round((time.time() - t0) * 1000)
                logger.error("[Pipeline|权限校验] 拒绝, ds_id=%d ds_name=%s status=%s elapsed=%dms",
                            ds_id, ds.name, ds.status, elapsed)
                return {
                    "status": "auth_failed",
                    "error_info": f"数据源不可用 (status={ds.status})",
                }

        elapsed = round((time.time() - t0) * 1000)
        logger.info("[Pipeline|权限校验] 通过, ds_id=%d ds_name=%s db_type=%s elapsed=%dms",
                    ds_id, ds.name, ds.db_type, elapsed)
        return {"status": "init"}
