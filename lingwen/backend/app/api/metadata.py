"""Metadata routes — manage business descriptions for tables and columns."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.metadata import (
    ColumnMetadataResponse,
    ColumnMetadataUpdate,
    TableMetadataResponse,
    TableMetadataUpdate,
)
from app.services import schema_service, metadata_service
from app.utils.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------
# Tables
# ------------------------------------------------------------------

@router.get("/tables", response_model=dict)
async def list_tables(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all table metadata records for a data source.

    Args:
        datasource_id: The data source ID.
        db: The database session (injected).

    Returns:
        A list of TableMetadataResponse objects.
    """
    tables = await schema_service.get_tables(db, datasource_id)
    result = [TableMetadataResponse.model_validate(t).model_dump() for t in tables]
    return success(data=result)


@router.put("/tables/{table_id}", response_model=dict)
async def update_table(
    table_id: int,
    payload: TableMetadataUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a table's display name or business description.

    Args:
        table_id: The primary key of the table metadata record.
        payload: Fields to update.
        db: The database session (injected).

    Returns:
        The updated TableMetadataResponse.
    """
    try:
        table = await metadata_service.update_table(
            db, table_id, payload.model_dump(exclude_unset=True)
        )
    except HTTPException:
        raise
    result = TableMetadataResponse.model_validate(table).model_dump()
    return success(data=result)


# ------------------------------------------------------------------
# Columns
# ------------------------------------------------------------------

@router.get("/columns", response_model=dict)
async def list_columns(
    table_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List all column metadata records for a table.

    Args:
        table_id: The primary key of the table metadata record.
        db: The database session (injected).

    Returns:
        A list of ColumnMetadataResponse objects.
    """
    columns = await schema_service.get_columns(db, table_id)
    result = [ColumnMetadataResponse.model_validate(c).model_dump() for c in columns]
    return success(data=result)


@router.put("/columns/{column_id}", response_model=dict)
async def update_column(
    column_id: int,
    payload: ColumnMetadataUpdate,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Update a column's display name, description, or enum values.

    Args:
        column_id: The primary key of the column metadata record.
        payload: Fields to update.
        db: The database session (injected).

    Returns:
        The updated ColumnMetadataResponse.
    """
    try:
        column = await metadata_service.update_column(
            db, column_id, payload.model_dump(exclude_unset=True)
        )
    except HTTPException:
        raise
    result = ColumnMetadataResponse.model_validate(column).model_dump()
    return success(data=result)
