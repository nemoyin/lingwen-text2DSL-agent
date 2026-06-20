"""Few-shot example routes — CRUD with ChromaDB index sync."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.few_shot import FewShotCreate, FewShotResponse, FewShotUpdate
from app.services import few_shot_service
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_indexer():
    """Lazy-load the Indexer from the global agent's components."""
    from app.api.deps import get_agent as _ga
    # We need an async context here, but get_agent() is designed to be called
    # within a route handler.  Since sync helpers can't await, we return a
    # factory-style approach: the route handler creates the indexer itself.
    return None


async def _sync_fewshot_to_chroma(fewshot) -> None:
    """Re-index a single few-shot example into ChromaDB.

    Args:
        fewshot: A :class:`FewShotExample` ORM object.
    """
    try:
        from app.rag.indexer import Indexer

        # Access the agent singleton to get the embedding client and vector store
        from app.api.deps import get_agent
        agent = await get_agent()
        indexer = Indexer(agent._embed_client, agent._vector_store)
        await indexer.index_fewshot(fewshot)
        logger.info("Few-shot %d synced to ChromaDB", fewshot.id)
    except Exception as exc:
        logger.error("Failed to sync few-shot %d to ChromaDB: %s", fewshot.id, exc)


@router.get("/", response_model=dict)
async def list_fewshots(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all few-shot examples for a data source.

    Args:
        datasource_id: The data source ID.
        db: The database session (injected).

    Returns:
        A list of FewShotResponse objects.
    """
    items = await few_shot_service.get_all(db, datasource_id)
    result = [FewShotResponse.model_validate(fs).model_dump() for fs in items]
    return success(data=result)


@router.post("/", response_model=dict)
async def create_fewshot(
    payload: FewShotCreate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a new few-shot example and index it in ChromaDB.

    Args:
        payload: The few-shot data (question, sql, etc.).
        db: The database session (injected).

    Returns:
        The created FewShotResponse.
    """
    try:
        fewshot = await few_shot_service.create(db, payload.model_dump())
    except HTTPException:
        raise

    # Sync to ChromaDB asynchronously (fire-and-forget with error logging)
    await _sync_fewshot_to_chroma(fewshot)

    result = FewShotResponse.model_validate(fewshot).model_dump()
    return success(data=result)


@router.get("/{fewshot_id}", response_model=dict)
async def get_fewshot(
    fewshot_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retrieve a single few-shot example by ID.

    Args:
        fewshot_id: The primary key of the example.
        db: The database session (injected).

    Returns:
        The FewShotResponse.

    Raises:
        HTTPException(404): If not found.
    """
    from app.models.few_shot import FewShotExample
    from sqlalchemy import select

    result_set = await db.execute(
        select(FewShotExample).where(FewShotExample.id == fewshot_id)
    )
    found = result_set.scalars().first()
    if found is None:
        raise HTTPException(status_code=404, detail="Few-shot 示例不存在")
    result = FewShotResponse.model_validate(found).model_dump()
    return success(data=result)


@router.put("/{fewshot_id}", response_model=dict)
async def update_fewshot(
    fewshot_id: int,
    payload: FewShotUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a few-shot example and re-sync its ChromaDB index.

    Args:
        fewshot_id: The primary key of the example.
        payload: Fields to update.
        db: The database session (injected).

    Returns:
        The updated FewShotResponse.
    """
    try:
        fewshot = await few_shot_service.update(
            db, fewshot_id, payload.model_dump(exclude_unset=True)
        )
    except HTTPException:
        raise

    # Re-sync to ChromaDB
    await _sync_fewshot_to_chroma(fewshot)

    result = FewShotResponse.model_validate(fewshot).model_dump()
    return success(data=result)


@router.delete("/{fewshot_id}", response_model=dict)
async def delete_fewshot(
    fewshot_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a few-shot example.

    Args:
        fewshot_id: The primary key of the example.
        db: The database session (injected).

    Returns:
        A confirmation message.
    """
    try:
        await few_shot_service.delete(db, fewshot_id)
    except HTTPException:
        raise

    # Remove from ChromaDB
    try:
        from app.api.deps import get_agent
        agent = await get_agent()
        doc_id = f"fewshot_{fewshot_id}"
        agent._vector_store.fewshot_col.delete(ids=[doc_id])
        logger.info("Few-shot %d deleted from ChromaDB", fewshot_id)
    except Exception as exc:
        logger.warning("Failed to delete few-shot %d from ChromaDB: %s", fewshot_id, exc)

    return success(data=None, message="Few-shot 示例已删除")
