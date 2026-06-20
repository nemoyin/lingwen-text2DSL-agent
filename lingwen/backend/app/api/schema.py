"""Schema routes — scan and browse external database schemas."""

import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.schema import SchemaScanRequest, ScanResult
from app.services import schema_service
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=dict)
async def list_schemas(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all tables and their columns for a data source.

    Args:
        datasource_id: The data source ID to query.
        db: The database session (injected).

    Returns:
        A nested list of tables, each with its columns::

            [{"table": {...}, "columns": [{...}, ...]}, ...]
    """
    tables = await schema_service.get_tables(db, datasource_id)
    result: List[Dict] = []

    for table in tables:
        columns = await schema_service.get_columns(db, table.id)
        result.append({
            "table": {
                "id": table.id,
                "datasource_id": table.datasource_id,
                "table_name": table.table_name,
                "display_name": table.display_name,
                "business_description": table.business_description,
                "created_at": str(table.created_at) if table.created_at else None,
                "updated_at": str(table.updated_at) if table.updated_at else None,
            },
            "columns": [
                {
                    "id": col.id,
                    "table_id": col.table_id,
                    "column_name": col.column_name,
                    "display_name": col.display_name,
                    "data_type": col.data_type,
                    "business_description": col.business_description,
                    "enum_values": col.enum_values,
                    "is_primary_key": col.is_primary_key,
                    "is_foreign_key": col.is_foreign_key,
                    "foreign_ref": col.foreign_ref,
                    "created_at": str(col.created_at) if col.created_at else None,
                    "updated_at": str(col.updated_at) if col.updated_at else None,
                }
                for col in columns
            ],
        })

    return success(data=result)


@router.post("/scan", response_model=dict)
async def scan_schema(
    payload: SchemaScanRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Trigger a schema scan for a data source.

    Reads ``information_schema`` from the target database and upserts
    table/column metadata.

    Args:
        payload: Contains ``datasource_id``.
        db: The database session (injected).

    Returns:
        A ScanResult summary.
    """
    try:
        result: ScanResult = await schema_service.scan(db, payload.datasource_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Schema scan failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Schema 扫描失败: {str(exc)}")

    return success(data=result.model_dump())
