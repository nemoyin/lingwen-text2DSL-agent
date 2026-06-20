"""Alerts API — create, list, escalate to case."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_current_user
from app.utils.response import success

router = APIRouter()


@router.post("")
async def create_alert(
    target_unit: str = "",
    content: str = "",
    query_id: int = 0,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    result = await db.execute(
        text("INSERT INTO alerts (user_id, query_id, target_unit, content) VALUES (:uid, :qid, :tu, :ct)"),
        {"uid": user["user_id"], "qid": query_id or None, "tu": target_unit, "ct": content}
    )
    await db.commit()
    return success(data={"id": result.lastrowid})


@router.get("")
async def list_alerts(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    result = await db.execute(
        text("SELECT * FROM alerts WHERE user_id=:uid ORDER BY created_at DESC"),
        {"uid": user["user_id"]}
    )
    items = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    for item in items:
        for k in ("created_at", "updated_at"):
            if item.get(k):
                item[k] = str(item[k])
    return success(data=items)


@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: int,
    is_filed: int = 1,
    case_number: str = "",
    handler: str = "",
    notes: str = "",
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        text("INSERT INTO cases (alert_id, is_filed, case_number, handler, notes) VALUES (:aid, :f, :cn, :h, :n)"),
        {"aid": alert_id, "f": is_filed, "cn": case_number, "h": handler, "n": notes}
    )
    await db.commit()
    return success(data={"id": result.lastrowid})


@router.get("/cases")
async def list_cases(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(
        text("SELECT c.*, a.target_unit, a.content as alert_content FROM cases c JOIN alerts a ON c.alert_id=a.id ORDER BY c.created_at DESC")
    )
    items = [dict(zip(result.keys(), row)) for row in result.fetchall()]
    for item in items:
        for k in ("created_at", "updated_at"):
            if item.get(k):
                item[k] = str(item[k])
    return success(data=items)
