"""Dashboard stats + trends + performance endpoint."""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.datasource import DataSource
from app.models.query_history import QueryHistory
from app.models.table_metadata import TableMetadata
from app.models.few_shot import FewShotExample
from app.services import history_service
from app.utils.response import success

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    user_count = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    ds_count = (await db.execute(select(func.count()).select_from(DataSource))).scalar() or 0
    q_count = (await db.execute(select(func.count()).select_from(QueryHistory))).scalar() or 0
    t_count = (await db.execute(select(func.count()).select_from(TableMetadata))).scalar() or 0
    f_count = (await db.execute(select(func.count()).select_from(FewShotExample))).scalar() or 0
    today_count = (await db.execute(select(func.count()).select_from(QueryHistory).where(func.date(QueryHistory.created_at) == func.curdate()))).scalar() or 0
    alert_count = (await db.execute(text("SELECT COUNT(*) FROM alerts"))).scalar() or 0
    case_count = (await db.execute(text("SELECT COUNT(*) FROM cases"))).scalar() or 0
    filed_count = (await db.execute(text("SELECT COUNT(*) FROM cases WHERE is_filed=1"))).scalar() or 0
    return success(data={
        "users": user_count, "datasources": ds_count, "queries": q_count,
        "tables": t_count, "fewshots": f_count, "today_queries": today_count,
        "alerts": alert_count, "cases": case_count, "filed_cases": filed_count,
    })


@router.get("/stats/trends")
async def get_trends(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    trends = await history_service.get_trends(db, 30)
    return success(data=trends)


@router.get("/stats/performance")
async def get_performance(db: AsyncSession = Depends(get_db), user: dict = Depends(get_current_user)) -> dict:
    """Return aggregated performance & interaction metrics for dashboard."""
    # -- Token stats (parse result_json.total_tokens) --
    token_result = await db.execute(text("""
        SELECT
            COALESCE(SUM(CAST(JSON_EXTRACT(result_json, '$.total_tokens') AS UNSIGNED)), 0) AS total_tokens,
            COALESCE(AVG(CAST(JSON_EXTRACT(result_json, '$.total_tokens') AS UNSIGNED)), 0) AS avg_tokens,
            COALESCE(MAX(CAST(JSON_EXTRACT(result_json, '$.total_tokens') AS UNSIGNED)), 0) AS max_tokens,
            COUNT(*) AS total_queries
        FROM query_history
        WHERE result_json IS NOT NULL AND status = 'completed'
    """))
    tk = token_result.fetchone()

    # -- Daily token trend (last 30 days) --
    token_trend_result = await db.execute(text("""
        SELECT
            DATE(created_at) AS d,
            COALESCE(SUM(CAST(JSON_EXTRACT(result_json, '$.total_tokens') AS UNSIGNED)), 0) AS tokens,
            COUNT(*) AS queries,
            ROUND(COALESCE(AVG(CAST(JSON_EXTRACT(result_json, '$.total_tokens') AS UNSIGNED)), 0)) AS avg_tokens
        FROM query_history
        WHERE result_json IS NOT NULL AND status = 'completed'
          AND created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY d ORDER BY d
    """))
    token_trend = [{
        "date": str(r[0]), "tokens": int(r[1]), "queries": int(r[2]), "avg_tokens": int(r[3])
    } for r in token_trend_result.fetchall()]

    # -- Latency stats --
    latency_result = await db.execute(text("""
        SELECT
            COALESCE(MIN(latency_ms), 0) AS min_latency,
            COALESCE(MAX(latency_ms), 0) AS max_latency,
            COALESCE(AVG(latency_ms), 0) AS avg_latency
        FROM query_history
        WHERE latency_ms IS NOT NULL AND latency_ms > 0 AND status = 'completed'
    """))
    lat = latency_result.fetchone()

    # -- Daily latency trend --
    latency_trend_result = await db.execute(text("""
        SELECT
            DATE(created_at) AS d,
            ROUND(MIN(latency_ms)) AS min_ms,
            ROUND(MAX(latency_ms)) AS max_ms,
            ROUND(AVG(latency_ms)) AS avg_ms
        FROM query_history
        WHERE latency_ms IS NOT NULL AND latency_ms > 0 AND status = 'completed'
          AND created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        GROUP BY d ORDER BY d
    """))
    latency_trend = [{
        "date": str(r[0]), "min_ms": int(r[1]), "max_ms": int(r[2]), "avg_ms": int(r[3])
    } for r in latency_trend_result.fetchall()]

    # -- Pipeline step aggregated metrics (parse pipeline_steps from result_json) --
    pipeline_result = await db.execute(text("""
        SELECT
            COALESCE(AVG(CAST(JSON_EXTRACT(result_json, '$.pipeline_steps[*].elapsed_ms') AS UNSIGNED)), 0) AS avg_step_ms,
            COALESCE(AVG(JSON_LENGTH(result_json, '$.pipeline_steps')), 0) AS avg_step_count
        FROM query_history
        WHERE result_json IS NOT NULL AND status = 'completed'
    """))
    pl = pipeline_result.fetchone()

    # -- Interaction stats --
    interaction_result = await db.execute(text("""
        SELECT
            COALESCE(SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END), 0) AS likes,
            COALESCE(SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END), 0) AS dislikes,
            COALESCE(SUM(CASE WHEN share_token IS NOT NULL THEN 1 ELSE 0 END), 0) AS shares
        FROM query_history
    """))
    inter = interaction_result.fetchone()

    return success(data={
        "tokens": {
            "total": int(tk[0]) if tk else 0,
            "avg_per_query": int(tk[1]) if tk else 0,
            "max_per_query": int(tk[2]) if tk else 0,
            "total_queries": int(tk[3]) if tk else 0,
        },
        "token_trend": token_trend,
        "latency": {
            "min_ms": int(lat[0]) if lat else 0,
            "max_ms": int(lat[1]) if lat else 0,
            "avg_ms": int(lat[2]) if lat else 0,
        },
        "latency_trend": latency_trend,
        "pipeline": {
            "avg_step_ms": int(pl[0]) if pl else 0,
            "avg_step_count": round(float(pl[1]) if pl else 0, 1),
        },
        "interactions": {
            "likes": int(inter[0]) if inter else 0,
            "dislikes": int(inter[1]) if inter else 0,
            "shares": int(inter[2]) if inter else 0,
        },
    })
