"""Core query routes — POST /api/query (sync) + POST /api/query/stream (SSE)."""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_agent, get_current_user, get_db
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.services import history_service
from app.utils.response import success

logger = logging.getLogger(__name__)


def _json_serialize(obj):
    """Convert Decimal/datetime for JSON-safe SSE streaming."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


router = APIRouter()


@router.post("/query", response_model=dict)
async def execute_query(
    payload: QueryRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Execute a natural-language query through the full Agent pipeline.

    Steps:
        1. Validate authentication via ``get_current_user``.
        2. Create a ``QueryService`` wrapping the singleton ``QueryAgent``.
        3. Run the pipeline (intent → perm check → RAG → SQL gen → ...).
        4. Record the query in history.
        5. Return the structured response.

    Args:
        payload: The query request (question + datasource_id).
        user: The authenticated user dict (injected).
        db: The database session (injected).

    Returns:
        A QueryResponse wrapped in ApiResponse.
    """
    user_id: int = user.get("user_id", 0)
    question: str = payload.question
    datasource_id: int = payload.datasource_id
    history = payload.history or []
    max_turns = payload.max_context_turns

    logger.info(
        "Query endpoint: user=%d ds=%d question=%s history_turns=%d",
        user_id, datasource_id, question[:100], len(history),
    )

    # Get the agent singleton
    agent = await get_agent()
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent 尚未初始化")

    # Create query service and execute
    query_service = QueryService(agent)
    try:
        result = await query_service.execute(question, datasource_id, user_id, history, max_turns)
        logger.info("Query result keys: %s, pipeline_steps=%d", list(result.keys()), len(result.get("pipeline_steps", [])))
    except Exception as exc:
        logger.error("Query execution failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"查询执行失败: {str(exc)}")

    # Record history
    history_id: Optional[int] = None
    try:
        status = "success" if result.get("data") is not None else "failed"
        record = await history_service.create_query_record(
            db=db,
            user_id=user_id,
            datasource_id=datasource_id,
            question=question,
            generated_sql=result.get("sql", ""),
            executed_sql=result.get("sql", ""),
            status=status,
            latency_ms=result.get("latency_ms", 0),
            row_count=result.get("row_count", 0),
            error_info=None,
            result_data=result if status == "success" else None,
        )
        history_id = record.id
    except Exception as exc:
        logger.warning("Failed to record query history: %s", exc)

    response = QueryResponse(
        question=result.get("question", question),
        data=result.get("data", []),
        columns=result.get("columns", []),
        analysis=result.get("analysis", ""),
        sql=result.get("sql", ""),
        chart_suggestion=result.get("chart_suggestion"),
        row_count=result.get("row_count", 0),
        is_truncated=result.get("is_truncated", False),
        latency_ms=result.get("latency_ms", 0),
        pipeline_steps=result.get("pipeline_steps", []),
        total_tokens=result.get("total_tokens", 0),
        suggested_questions=result.get("suggested_questions", []),
        history_id=history_id,
    )

    return success(data=response.model_dump())


@router.post("/query/stream")
async def execute_query_stream(
    payload: QueryRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Execute query with SSE streaming progress events.

    Each event is ``data: {json}\\n\\n``.  Steps are emitted as they
    complete, followed by ``event: done`` with the full result, then
    ``event: history_id`` with the saved history record ID.
    """
    user_id: int = user.get("user_id", 0)
    question: str = payload.question
    datasource_id: int = payload.datasource_id
    history = payload.history or []
    max_turns = payload.max_context_turns

    logger.info("Query stream: user=%d ds=%d question=%s", user_id, datasource_id, question[:100])

    agent = await get_agent()
    if agent is None:
        raise HTTPException(status_code=500, detail="Agent 尚未初始化")

    async def event_generator():
        final_data: Optional[dict] = None
        try:
            async for evt in agent.run_stream(question, datasource_id, user_id, history, max_turns):
                if evt.get("event") == "done":
                    final_data = evt.get("data", {})
                yield f"data: {json.dumps(evt, ensure_ascii=False, default=_json_serialize)}\n\n"
        except Exception as exc:
            logger.error("Stream query failed: %s", exc)
            yield f"data: {json.dumps({'event': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"
            return  # Don't record history on failure

        # Record history after stream completes successfully
        if final_data:
            try:
                status = "success" if final_data.get("data") is not None else "failed"
                record = await history_service.create_query_record(
                    db=db,
                    user_id=user_id,
                    datasource_id=datasource_id,
                    question=question,
                    generated_sql=final_data.get("sql", ""),
                    executed_sql=final_data.get("sql", ""),
                    status=status,
                    latency_ms=final_data.get("latency_ms", 0),
                    row_count=final_data.get("row_count", 0),
                    error_info=None,
                    result_data=final_data if status == "success" else None,
                )
                yield f"data: {json.dumps({'event': 'history_id', 'id': record.id}, ensure_ascii=False)}\n\n"
                logger.info("Stream history recorded: id=%d", record.id)
            except Exception as exc:
                logger.warning("Failed to record stream query history: %s", exc)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
