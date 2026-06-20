"""Query history routes — browse past queries."""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.services import history_service
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/history", response_model=dict)
async def list_history(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页条数"),
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    """Paginate query history for the current user."""
    try:
        user_id = user["user_id"]
        result = await history_service.get_history(db, user_id, page, page_size)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("History query failed: %s", exc)
        raise HTTPException(status_code=500, detail="查询历史获取失败")

    items = []
    for record in result["items"]:
        items.append({
            "id": record.id,
            "question": record.question,
            "generated_sql": record.generated_sql,
            "status": record.status,
            "latency_ms": record.latency_ms,
            "row_count": record.row_count,
            "error_message": record.error_message,
            "result_json": record.result_json,
            "feedback": record.feedback,
            "share_token": record.share_token,
            "created_at": str(record.created_at) if record.created_at else None,
        })

    return success(data={
        "items": items,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
    })
