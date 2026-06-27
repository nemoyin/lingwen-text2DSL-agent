"""Benchmark API — upload test sets, create and execute evaluation runs."""
import json, csv, io, time, logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api.deps import get_db, get_current_user
from app.utils.response import success

logger = logging.getLogger(__name__)
router = APIRouter()

def _asdict(row):
    return dict(row._mapping)


@router.post("/sets")
async def upload_set(
    file: UploadFile = File(...),
    name: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))
    rows = [(r.get("question", ""), r.get("expected_answer", "")) for r in reader if r.get("question", "").strip()]
    if not rows:
        raise HTTPException(400, "CSV 中无有效数据（需 question, expected_answer 列）")
    set_name = name or file.filename.rsplit(".", 1)[0]
    result = await db.execute(text("INSERT INTO benchmark_sets (name, row_count) VALUES (:n, :c)"), {"n": set_name, "c": len(rows)})
    await db.commit()
    set_id = result.lastrowid
    for q, a in rows:
        await db.execute(text("INSERT INTO benchmark_questions (set_id, question, expected_answer) VALUES (:s,:q,:a)"), {"s": set_id, "q": q, "a": a})
    await db.commit()
    return success(data={"id": set_id, "name": set_name, "row_count": len(rows)})


@router.get("/sets")
async def list_sets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM benchmark_sets ORDER BY id DESC"))
    return success(data=[_asdict(r) for r in result.fetchall()])


@router.delete("/sets/{set_id}")
async def delete_set(set_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(text("DELETE FROM benchmark_sets WHERE id=:id"), {"id": set_id})
    await db.commit()
    return success(message="已删除")


@router.post("/runs")
async def create_run(set_id: int = Query(...), datasource_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("INSERT INTO benchmark_runs (set_id, datasource_id, status) VALUES (:s,:d,'pending')"), {"s": set_id, "d": datasource_id})
    await db.commit()
    return success(data={"id": result.lastrowid})


@router.get("/runs")
async def list_runs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text(
        "SELECT r.*, s.name as set_name FROM benchmark_runs r JOIN benchmark_sets s ON r.set_id=s.id ORDER BY r.id DESC"
    ))
    return success(data=[_asdict(r) for r in result.fetchall()])


@router.get("/runs/{run_id}")
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT * FROM benchmark_runs WHERE id=:id"), {"id": run_id})
    run = result.fetchone()
    if not run:
        raise HTTPException(404)
    run_dict = _asdict(run)
    if run_dict.get("created_at"):
        run_dict["created_at"] = str(run_dict["created_at"])
    r2 = await db.execute(text("SELECT * FROM benchmark_results WHERE run_id=:id ORDER BY id"), {"id": run_id})
    run_dict["results"] = [_asdict(r) for r in r2.fetchall()]
    return success(data=run_dict)


@router.post("/runs/{run_id}/execute")
async def execute_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    from app.agent.graph import QueryAgent
    from app.services.model_service import ModelService, build_llm

    run_row = (await db.execute(text("SELECT * FROM benchmark_runs WHERE id=:id"), {"id": run_id})).fetchone()
    if not run_row:
        raise HTTPException(404)
    run = _asdict(run_row)
    set_id = run["set_id"]
    ds_id = run["datasource_id"]

    await db.execute(text("UPDATE benchmark_runs SET status='running' WHERE id=:id"), {"id": run_id})
    await db.commit()

    questions = (await db.execute(text("SELECT * FROM benchmark_questions WHERE set_id=:s"), {"s": set_id})).fetchall()

    # Resolve the active default model for this benchmark run
    model_config = await ModelService.get_default(db)
    llm = build_llm(model_config) if model_config else None
    agent = QueryAgent(llm=llm)
    passed = total = 0

    for q_row in questions:
        q = _asdict(q_row)
        total += 1
        t0 = time.time()
        try:
            result = await agent.run(q["question"], ds_id, user["user_id"])
            latency = round((time.time() - t0) * 1000)
            actual = result.get("analysis", "")
            actual_sql = result.get("sql", "")
            pipeline = json.dumps(result.get("pipeline_steps", []), ensure_ascii=False)
        except Exception as e:
            actual = f"ERROR: {e}"
            actual_sql = ""
            pipeline = "[]"
            latency = round((time.time() - t0) * 1000)

        expected = q.get("expected_answer") or ""
        score = _keyword_score(expected, actual)
        is_pass = 1 if score >= 0.3 else 0
        passed += is_pass

        await db.execute(text(
            "INSERT INTO benchmark_results (run_id, question, expected_answer, actual_answer, actual_sql, pipeline_json, latency_ms, similarity_score, passed) VALUES (:r,:q,:e,:a,:s,:p,:l,:sc,:pa)"
        ), {"r": run_id, "q": q["question"], "e": expected, "a": actual[:2000], "s": actual_sql[:2000], "p": pipeline, "l": latency, "sc": round(score, 2), "pa": is_pass})
        await db.commit()

    overall = round(passed / total * 100, 2) if total > 0 else 0
    await db.execute(text(
        "UPDATE benchmark_runs SET status='done', total_count=:t, passed_count=:p, score=:s WHERE id=:id"
    ), {"t": total, "p": passed, "s": overall, "id": run_id})
    await db.commit()

    return success(data={"score": overall, "passed": passed, "total": total})


def _keyword_score(expected: str, actual: str) -> float:
    # Error answers should never pass
    if actual.startswith("ERROR:") or "查询失败" in actual:
        return 0.0
    if not expected:
        return 0.5
    if expected.lower().strip() == actual.lower().strip():
        return 1.0
    words = [w for w in expected.lower().split() if len(w) > 1]
    if not words:
        return 0.3
    hits = sum(1 for w in words if w in actual.lower())
    return min(hits / len(words), 1.0)
