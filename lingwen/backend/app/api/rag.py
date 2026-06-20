"""RAG management routes — reindex schemas/few-shots into ChromaDB."""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import DataSource, TableMetadata, ColumnMetadata, FewShotExample
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/reindex", response_model=dict)
async def reindex_all(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    """Rebuild ChromaDB vector indexes for all data sources.

    Purges all existing embeddings, then re-indexes every datasource's
    table schemas and few-shot examples using the current embedding model.

    Returns:
        Summary of indexed counts per datasource.
    """
    try:
        from app.api.deps import get_agent
        from app.rag.indexer import Indexer

        agent = await get_agent()
        indexer = Indexer(agent._embed_client, agent._vector_store)

        # Load all datasources with their tables/columns and few-shots
        stmt = (
            select(DataSource)
            .options(
                selectinload(DataSource.tables).selectinload(TableMetadata.columns),
                selectinload(DataSource.few_shot_examples),
            )
            .where(DataSource.status == "active")
        )
        result = await db.execute(stmt)
        datasources = result.scalars().all()

        summary: Dict[str, dict] = {}

        for ds in datasources:
            # Build columns_by_table mapping
            columns_by_table: Dict[str, List] = {}
            for table in ds.tables:
                columns_by_table[table.table_name] = table.columns

            # Also load few-shot examples
            fw_stmt = select(FewShotExample).where(
                FewShotExample.datasource_id == ds.id
            )
            fw_result = await db.execute(fw_stmt)
            fewshot_examples = fw_result.scalars().all()

            try:
                counts = await indexer.index_all(
                    datasource_id=ds.id,
                    tables=ds.tables,
                    columns_by_table=columns_by_table,
                    fewshot_examples=fewshot_examples,
                )
                summary[ds.name] = counts
                logger.info(
                    "[RAG|Reindex] datasource=%s id=%d schemas=%d fewshots=%d",
                    ds.name, ds.id, counts["schemas"], counts["fewshots"],
                )
            except Exception as exc:
                logger.error(
                    "[RAG|Reindex] FAILED datasource=%s id=%d: %s",
                    ds.name, ds.id, exc,
                )
                summary[ds.name] = {"error": str(exc)}

        total_schemas = sum(s.get("schemas", 0) for s in summary.values() if isinstance(s.get("schemas"), int))
        total_fewshots = sum(s.get("fewshots", 0) for s in summary.values() if isinstance(s.get("fewshots"), int))

        logger.info(
            "[RAG|Reindex] COMPLETE — %d datasources, %d schemas, %d fewshots",
            len(summary), total_schemas, total_fewshots,
        )

        return success(data={
            "datasources": summary,
            "total_schemas": total_schemas,
            "total_fewshots": total_fewshots,
        })

    except Exception as exc:
        logger.error("[RAG|Reindex] ERROR: %s", exc)
        raise HTTPException(status_code=500, detail=f"重建索引失败: {str(exc)}")


@router.post("/reindex/{datasource_id}", response_model=dict)
async def reindex_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    """Rebuild ChromaDB vector indexes for a single data source.

    Args:
        datasource_id: The data source to reindex.

    Returns:
        Summary of indexed counts.
    """
    try:
        from app.api.deps import get_agent
        from app.rag.indexer import Indexer

        # Load datasource with tables/columns
        stmt = (
            select(DataSource)
            .options(
                selectinload(DataSource.tables).selectinload(TableMetadata.columns),
            )
            .where(DataSource.id == datasource_id)
        )
        result = await db.execute(stmt)
        ds = result.scalars().first()

        if not ds:
            raise HTTPException(status_code=404, detail="数据源不存在")

        # Load few-shots
        fw_stmt = select(FewShotExample).where(
            FewShotExample.datasource_id == datasource_id
        )
        fw_result = await db.execute(fw_stmt)
        fewshot_examples = fw_result.scalars().all()

        agent = await get_agent()
        indexer = Indexer(agent._embed_client, agent._vector_store)

        columns_by_table: Dict[str, List] = {}
        for table in ds.tables:
            columns_by_table[table.table_name] = table.columns

        counts = await indexer.index_all(
            datasource_id=ds.id,
            tables=ds.tables,
            columns_by_table=columns_by_table,
            fewshot_examples=fewshot_examples,
        )

        logger.info(
            "[RAG|Reindex] datasource=%s id=%d schemas=%d fewshots=%d",
            ds.name, ds.id, counts["schemas"], counts["fewshots"],
        )

        return success(data=counts)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[RAG|Reindex] ERROR ds=%d: %s", datasource_id, exc)
        raise HTTPException(status_code=500, detail=f"重建索引失败: {str(exc)}")


@router.get("/status", response_model=dict)
async def rag_status(
    user: dict = Depends(get_current_user),
) -> dict:
    """Check ChromaDB vector store status.

    Returns:
        Document counts in schema and fewshot collections.
    """
    try:
        from app.api.deps import get_agent

        agent = await get_agent()
        schema_count = agent._vector_store.count_schemas()
        fewshot_count = agent._vector_store.count_fewshots()

        return success(data={
            "schema_count": schema_count,
            "fewshot_count": fewshot_count,
        })
    except Exception as exc:
        logger.error("[RAG|Status] ERROR: %s", exc)
        raise HTTPException(status_code=500, detail=f"查询RAG状态失败: {str(exc)}")
