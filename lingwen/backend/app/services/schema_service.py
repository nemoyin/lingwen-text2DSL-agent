"""Schema scanning service — dispatches to the correct adapter and UPSERTs metadata."""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.column_metadata import ColumnMetadata
from app.models.datasource import DataSource
from app.models.table_metadata import TableMetadata
from app.schemas.schema import ScanResult
from app.services import datasource_service
from app.security.encrypt import decrypt_password
from app.adapters import get_adapter
from app.adapters.base import ConnectionParams

logger = logging.getLogger(__name__)


def _build_params(ds: DataSource) -> ConnectionParams:
    """Build ConnectionParams from a DataSource ORM row."""
    password = decrypt_password(ds.password_encrypted)
    return ConnectionParams(
        host=ds.host,
        port=ds.port,
        database=ds.database,
        username=ds.username,
        password=password,
        extra_params=ds.extra_params if hasattr(ds, "extra_params") and ds.extra_params else {},
    )


async def scan(db: AsyncSession, datasource_id: int) -> ScanResult:
    """Scan a data source's schema using the registered adapter and upsert metadata.

    Steps:
        1. Fetch the data source record.
        2. Get the adapter for this ``db_type``.
        3. Call ``adapter.scan_tables()`` and ``adapter.scan_columns()``.
        4. UPSERT rows in ``tables_metadata`` and ``columns_metadata``.

    Args:
        db: The database session (for the metadata store).
        datasource_id: The primary key of the data source to scan.

    Returns:
        A :class:`ScanResult` summarising the scan.
    """
    ds = await datasource_service.get(db, datasource_id)
    adapter = get_adapter(ds.db_type)
    params = _build_params(ds)

    scanned_at = datetime.now()
    tables_added = 0
    tables_updated = 0
    columns_added = 0
    columns_updated = 0

    # Delegate schema introspection to the adapter
    schema_tables = await adapter.scan_tables(params)
    schema_columns = await adapter.scan_columns(params)

    tables_scanned = len(schema_tables)
    columns_scanned = len(schema_columns)

    # Group columns by table name
    columns_by_table: dict[str, list] = {}
    for col in schema_columns:
        columns_by_table.setdefault(col.table_name, []).append(col)

    # ---- UPSERT tables ----
    for st in schema_tables:
        tname = st.table_name
        tcomment = st.table_comment

        # Check if table already exists
        result = await db.execute(
            select(TableMetadata).where(
                TableMetadata.datasource_id == datasource_id,
                TableMetadata.table_name == tname,
            )
        )
        existing = result.scalars().first()

        if existing:
            existing.table_name = tname
            if tcomment:
                existing.business_description = tcomment
            tables_updated += 1
        else:
            tbl = TableMetadata(
                datasource_id=datasource_id,
                table_name=tname,
                business_description=tcomment,
            )
            db.add(tbl)
            tables_added += 1
            await db.flush()

        # ---- UPSERT columns for this table ----
        for sc in columns_by_table.get(tname, []):
            # Re-fetch to ensure we have the latest table ID
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
                    ColumnMetadata.column_name == sc.column_name,
                )
            )
            existing_col = result.scalars().first()

            if existing_col:
                existing_col.data_type = sc.data_type
                if sc.comment:
                    existing_col.business_description = sc.comment
                existing_col.is_primary_key = sc.is_primary_key
                columns_updated += 1
            else:
                col_meta = ColumnMetadata(
                    table_id=tbl_meta.id,
                    column_name=sc.column_name,
                    data_type=sc.data_type,
                    business_description=sc.comment,
                    is_primary_key=sc.is_primary_key,
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
