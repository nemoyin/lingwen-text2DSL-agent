"""User settings API — theme, language."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_current_user
from app.utils.response import success

router = APIRouter()


@router.get("/settings")
async def get_settings(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    result = await db.execute(text("SELECT * FROM user_settings WHERE user_id=:uid"), {"uid": user["user_id"]})
    row = result.fetchone()
    if not row:
        await db.execute(text("INSERT INTO user_settings (user_id, theme, language) VALUES (:uid, 'light', 'zh')"), {"uid": user["user_id"]})
        await db.commit()
        return success(data={"theme": "light", "language": "zh"})
    return success(data=dict(zip(result.keys(), row)))


@router.put("/settings")
async def update_settings(
    theme: str = "light",
    language: str = "zh",
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    await db.execute(
        text("INSERT INTO user_settings (user_id, theme, language) VALUES (:uid, :t, :l) ON DUPLICATE KEY UPDATE theme=:t2, language=:l2"),
        {"uid": user["user_id"], "t": theme, "l": language, "t2": theme, "l2": language}
    )
    await db.commit()
    return success(data={"theme": theme, "language": language})
