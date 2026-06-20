"""Extended history routes — delete, feedback."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_user
from app.services import history_service
from app.utils.response import success

router = APIRouter()


@router.delete("/{record_id}")
async def delete_history(record_id: int, db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    ok = await history_service.delete_record(db, record_id, user["user_id"])
    if not ok:
        raise HTTPException(404, "记录不存在")
    return success(message="已删除")


@router.post("/{record_id}/feedback")
async def set_feedback(record_id: int, feedback: int = 1, db: AsyncSession = Depends(get_db)) -> dict:
    ok = await history_service.set_feedback(db, record_id, feedback)
    if not ok:
        raise HTTPException(404, "记录不存在")
    icon = "👍" if feedback == 1 else "👎"
    return success(message=f"已反馈 {icon}")
