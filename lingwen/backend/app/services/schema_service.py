"""Schema scanning service — read information_schema and UPSERT metadata."""

import logging
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.column_metadata import ColumnMetadata
from app.models.datasource import DataSource
from app.models.table_metadata import TableMetadata
from app.schemas.schema import ScanResult
from app.services import datasource_service

logger = logging.getLogger(__name__)


async def scan(db: AsyncSession, datasource_id: int) -> ScanResult:
    """Scan a data source's ``information_schema`` and upsert metadata.

    Steps:
        1. Fetch the data source record.
        2. Dynamically connect to the user's MySQL.
        3. Read ``TABLES`` and ``COLUMNS`` from ``information_schema``.
        4. UPSERT rows in ``tables_metadata`` and ``columns_metadata``.

    Args:
        db: The database session (for the metadata store).
        datasource_id: The primary key of the data source to scan.

    Returns:
        A :class:`ScanResult` summarising the scan.
    """
    ds = await datasource_service.get(db, datasource_id)
    engine = await datasource_service.get_connection(db, datasource_id)

    scanned_at = datetime.now()
    tables_added = 0
    tables_updated = 0
    columns_added = 0
    columns_updated = 0

    async with engine.connect() as conn:
        # ---- Read tables ----
        tables_result = await conn.execute(
            text(
                "SELECT TABLE_NAME, TABLE_COMMENT "
                "FROM information_schema.TABLES "
                "WHERE TABLE_SCHEMA = :db AND TABLE_TYPE = 'BASE TABLE'"
            ),
            {"db": ds.database},
        )
        table_rows = tables_result.fetchall()

        # ---- Read columns ----
        columns_result = await conn.execute(
            text(
                "SELECT "
                "  TABLE_NAME, COLUMN_NAME, DATA_TYPE, "
                "  IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT, "
                "  COLUMN_KEY "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = :db "
                "ORDER BY TABLE_NAME, ORDINAL_POSITION"
            ),
            {"db": ds.database},
        )
        column_rows = columns_result.fetchall()

    tables_scanned = len(table_rows)
    columns_scanned = len(column_rows)

    # Group columns by table name
    columns_by_table: dict[str, list] = {}
    for col in column_rows:
        tname = col[0]  # TABLE_NAME
        if tname not in columns_by_table:
            columns_by_table[tname] = []
        columns_by_table[tname].append(col)

    # ---- UPSERT tables ----
    for trow in table_rows:
        tname = trow[0]
        tcomment = trow[1] if trow[1] else None

        # Check if table already exists
        result = await db.execute(
            select(TableMetadata).where(
                TableMetadata.datasource_id == datasource_id,
                TableMetadata.table_name == tname,
            )
        )
        existing = result.scalars().first()

        if existing:
            # Update existing
            existing.table_name = tname
            if tcomment:
                existing.business_description = tcomment
            tables_updated += 1
        else:
            # Insert new
            tbl = TableMetadata(
                datasource_id=datasource_id,
                table_name=tname,
                business_description=tcomment,
            )
            db.add(tbl)
            tables_added += 1

            # Flush to get table.id for column foreign keys
            await db.flush()

        # ---- UPSERT columns for this table ----
        for crow in columns_by_table.get(tname, []):
            col_name = crow[1]
            data_type = crow[2]
            is_nullable = crow[3] == "YES"
            col_default = crow[4]
            col_comment = crow[5] if crow[5] else None
            col_key = crow[6]  # PRI / MUL / UNI / empty

            is_pk = col_key == "PRI"

            # Re-fetch the table to ensure we have the latest ID
            result = await db.execute(
                select(TableMetadata).where(
                    TableMetadata.datasource_id == datasource_id,
                    TableMetadata.table_name == tname,
                )
            )
            tbl_meta = result.scalars().first()
            if tbl_meta is None:
                continue

            # Check existing column
            result = await db.execute(
                select(ColumnMetadata).where(
                    ColumnMetadata.table_id == tbl_meta.id,
                    ColumnMetadata.column_name == col_name,
                )
            )
            existing_col = result.scalars().first()

            if existing_col:
                existing_col.data_type = data_type
                if col_comment:
                    existing_col.business_description = col_comment
                existing_col.is_primary_key = is_pk
                columns_updated += 1
            else:
                col_meta = ColumnMetadata(
                    table_id=tbl_meta.id,
                    column_name=col_name,
                    data_type=data_type,
                    business_description=col_comment,
                    is_primary_key=is_pk,
                )
                db.add(col_meta)
                columns_added += 1

    await db.commit()

    # Update datasource status
    ds.status = "active"
    await db.commit()

    logger.info(
        "Schema scan complete: ds_id=%d tables=%d/%d columns=%d/%d",
        datasource_id,
        tables_added + tables_updated,
        tables_scanned,
        columns_added + columns_updated,
        columns_scanned,
    )

    return ScanResult(
        datasource_id=datasource_id,
        tables_scanned=tables_scanned,
        columns_scanned=columns_scanned,
        tables_added=tables_added,
        tables_updated=tables_updated,
        columns_added=columns_added,
        columns_updated=columns_updated,
        scanned_at=scanned_at,
    )


async def get_tables(
    db: AsyncSession, datasource_id: int
) -> list[TableMetadata]:
    """Return all table metadata records for a data source.

    Args:
        db: The database session.
        datasource_id: The primary key of the data source.

    Returns:
        A list of :class:`TableMetadata` objects.
    """
    result = await db.execute(
        select(TableMetadata)
        .where(TableMetadata.datasource_id == datasource_id)
        .order_by(TableMetadata.table_name)
    )
    return list(result.scalars().all())


async def get_columns(
    db: AsyncSession, table_id: int
) -> list[ColumnMetadata]:
    """Return all column metadata records for a table.

    Args:
        db: The database session.
        table_id: The primary key of the table metadata record.

    Returns:
        A list of :class:`ColumnMetadata` objects.
    """
    result = await db.execute(
        select(ColumnMetadata)
        .where(ColumnMetadata.table_id == table_id)
        .order_by(ColumnMetadata.id)
    )
    return list(result.scalars().all())
