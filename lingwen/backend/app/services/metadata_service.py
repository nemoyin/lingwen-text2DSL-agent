"""Metadata management service — update table and column business semantics."""

import logging

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.column_metadata import ColumnMetadata
from app.models.table_metadata import TableMetadata

logger = logging.getLogger(__name__)


async def update_table(
    db: AsyncSession,
    table_id: int,
    data: dict,
) -> TableMetadata:
    """Update business metadata for a table.

    Args:
        db: The database session.
        table_id: Primary key of the table metadata record.
        data: Dict with optional ``display_name`` and ``business_description``.

    Returns:
        The updated :class:`TableMetadata` object.

    Raises:
        HTTPException(404): If the table is not found.
    """
    result = await db.execute(
        select(TableMetadata).where(TableMetadata.id == table_id)
    )
    table = result.scalars().first()
    if table is None:
        raise HTTPException(status_code=404, detail="表元数据不存在")

    if "display_name" in data:
        table.display_name = data["display_name"]
    if "business_description" in data:
        table.business_description = data["business_description"]

    await db.commit()
    await db.refresh(table)
    logger.info("Table metadata updated: id=%d", table_id)
    return table


async def update_column(
    db: AsyncSession,
    column_id: int,
    data: dict,
) -> ColumnMetadata:
    """Update business metadata for a column.

    Args:
        db: The database session.
        column_id: Primary key of the column metadata record.
        data: Dict with optional ``display_name``, ``business_description``,
            and ``enum_values``.

    Returns:
        The updated :class:`ColumnMetadata` object.

    Raises:
        HTTPException(404): If the column is not found.
    """
    result = await db.execute(
        select(ColumnMetadata).where(ColumnMetadata.id == column_id)
    )
    column = result.scalars().first()
    if column is None:
        raise HTTPException(status_code=404, detail="字段元数据不存在")

    if "display_name" in data:
        column.display_name = data["display_name"]
    if "business_description" in data:
        column.business_description = data["business_description"]
    if "enum_values" in data:
        column.enum_values = data["enum_values"]

    await db.commit()
    await db.refresh(column)
    logger.info("Column metadata updated: id=%d", column_id)
    return column
