"""Model management API — CRUD for LLM model configurations."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_current_user
from app.utils.response import success

logger = logging.getLogger(__name__)
router = APIRouter()

PROVIDERS = ["deepseek", "openai", "kimi", "glm", "minimax"]

def _asdict(row):
    return dict(row._mapping)


@router.get("/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM model_configs ORDER BY id"))
    return success(data=[_asdict(r) for r in result.fetchall()])


@router.get("/models/{model_id}")
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM model_configs WHERE id=:id"), {"id": model_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(404, "模型不存在")
    return success(data=_asdict(row))


@router.post("/models")
async def create_model(
    name: str = Query(...),
    provider: str = Query(...),
    model_name: str = Query(...),
    api_base: str = Query(...),
    api_key: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    if provider not in PROVIDERS:
        raise HTTPException(400, f"不支持的供应商: {provider}，支持: {', '.join(PROVIDERS)}")
    result = await db.execute(text(
        "INSERT INTO model_configs (name, provider, model_name, api_base, api_key) VALUES (:n,:p,:m,:b,:k)"
    ), {"n": name, "p": provider, "m": model_name, "b": api_base, "k": api_key})
    await db.commit()
    return success(data={"id": result.lastrowid})


@router.put("/models/{model_id}")
async def update_model(
    model_id: int,
    name: str = Query(None),
    provider: str = Query(None),
    model_name: str = Query(None),
    api_base: str = Query(None),
    api_key: str = Query(None),
    is_active: int = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if provider and provider not in PROVIDERS:
        raise HTTPException(400, f"不支持的供应商: {provider}")
    updates = []
    params = {"id": model_id}
    for field in ["name", "provider", "model_name", "api_base", "api_key", "is_active"]:
        val = locals().get(field)
        if val is not None:
            updates.append(f"{field}=:{field}")
            params[field] = val
    if not updates:
        raise HTTPException(400, "无更新字段")
    await db.execute(text(f"UPDATE model_configs SET {', '.join(updates)} WHERE id=:id"), params)
    await db.commit()
    return success(message="已更新")


@router.delete("/models/{model_id}")
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM model_configs WHERE id=:id"), {"id": model_id})
    await db.commit()
    return success(message="已删除")


@router.post("/models/{model_id}/set-default")
async def set_default(model_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(text("UPDATE model_configs SET is_default=0"))
    await db.execute(text("UPDATE model_configs SET is_default=1 WHERE id=:id"), {"id": model_id})
    await db.commit()
    return success(message="已设为默认")


@router.post("/models/{model_id}/test")
async def test_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM model_configs WHERE id=:id"), {"id": model_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(404)
    cfg = _asdict(row)
    try:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=cfg["model_name"],
            api_key=cfg["api_key"] or "no-key",
            base_url=cfg["api_base"],
            temperature=0.1,
            timeout=10,
        )
        resp = await llm.ainvoke([{"role": "user", "content": "Hello, reply with just the word OK"}])
        return success(data={"status": "ok", "response": str(resp.content)[:100]})
    except Exception as e:
        return success(data={"status": "error", "error": str(e)[:200]})
