"""Query history service — recording, listing, feedback, and deletion."""

import json
import logging
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query_history import QueryHistory

logger = logging.getLogger(__name__)


def _json_default(obj: Any) -> Any:
    """Convert non-serializable types (Decimal, datetime) for json.dumps."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


async def create_query_record(
    db: AsyncSession,
    user_id: int,
    datasource_id: int,
    question: str,
    generated_sql: str,
    executed_sql: str,
    status: str,
    latency_ms: float,
    row_count: int = 0,
    error_info: Optional[str] = None,
    result_data: Optional[dict] = None,
) -> QueryHistory:
    record = QueryHistory(
        user_id=user_id,
        datasource_id=datasource_id,
        question=question,
        generated_sql=generated_sql,
        executed_sql=executed_sql,
        status=status,
        latency_ms=int(latency_ms) if latency_ms else None,
        row_count=row_count,
        error_message=error_info,
        result_json=json.dumps(result_data, default=_json_default) if result_data else None,
        share_token=hashlib.md5(f"{user_id}{datetime.now().timestamp()}".encode()).hexdigest()[:8],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_history(db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    offset = (page - 1) * page_size
    total_result = await db.execute(select(func.count(QueryHistory.id)).where(QueryHistory.user_id == user_id))
    total: int = total_result.scalar() or 0
    result = await db.execute(
        select(QueryHistory).where(QueryHistory.user_id == user_id).order_by(QueryHistory.id.desc()).offset(offset).limit(page_size)
    )
    items: List[QueryHistory] = list(result.scalars().all())
    return {"items": items, "total": total, "page": page, "page_size": page_size, "total_pages": max((total + page_size - 1) // page_size, 1)}


async def get_by_id(db: AsyncSession, record_id: int) -> Optional[QueryHistory]:
    result = await db.execute(select(QueryHistory).where(QueryHistory.id == record_id))
    return result.scalars().first()


async def delete_record(db: AsyncSession, record_id: int, user_id: int) -> bool:
    result = await db.execute(sa_delete(QueryHistory).where(QueryHistory.id == record_id, QueryHistory.user_id == user_id))
    await db.commit()
    return result.rowcount > 0


async def set_feedback(db: AsyncSession, record_id: int, feedback: int) -> bool:
    record = await get_by_id(db, record_id)
    if not record:
        return False
    record.feedback = feedback
    await db.commit()
    return True


async def get_trends(db: AsyncSession, days: int = 30) -> list:
    from sqlalchemy import text
    result = await db.execute(
        text("SELECT DATE(created_at) as d, COUNT(*) as c FROM query_history WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL :days DAY) GROUP BY d ORDER BY d"),
        {"days": days}
    )
    return [{"date": str(r[0]), "count": r[1]} for r in result.fetchall()]
