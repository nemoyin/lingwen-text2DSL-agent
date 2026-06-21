"""Data source management service: CRUD, connection testing, dynamic engines."""

import logging
from typing import Dict, Optional

import aiomysql
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from app.models.datasource import DataSource
from app.schemas.datasource import DataSourceCreate, DataSourceUpdate
from app.security.encrypt import decrypt_password, encrypt_password
from app.config import settings
from app.adapters import get_adapter
from app.adapters.base import ConnectionParams

logger = logging.getLogger(__name__)

# Cache of dynamically created engines keyed by datasource id.
# Deleted datasources should have their engine disposed and removed.
_engine_cache: Dict[int, AsyncEngine] = {}


def _build_connection_params(ds: DataSource, password: str) -> ConnectionParams:
    """Build a ConnectionParams from a DataSource ORM row."""
    return ConnectionParams(
        host=ds.host,
        port=ds.port,
        database=ds.database,
        username=ds.username,
        password=password,
        extra_params=ds.extra_params if hasattr(ds, "extra_params") and ds.extra_params else {},
    )


async def create(db: AsyncSession, data: DataSourceCreate) -> DataSource:
    """Create a new data source record.

    Args:
        db: The database session.
        data: The data source creation payload.

    Returns:
        The newly created DataSource ORM object.

    Raises:
        HTTPException(409): If a data source with the same name already exists.
    """
    # Uniqueness check
    result = await db.execute(select(DataSource).where(DataSource.name == data.name))
    if result.scalars().first() is not None:
        raise HTTPException(status_code=409, detail="数据源名称已存在")

    ds = DataSource(
        name=data.name,
        db_type=data.db_type,
        host=data.host,
        port=data.port,
        database=data.database,
        username=data.username,
        password_encrypted=encrypt_password(data.password),
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    logger.info("DataSource created: id=%d name=%s", ds.id, ds.name)
    return ds


async def get(db: AsyncSession, ds_id: int) -> DataSource:
    """Retrieve a single data source by ID.

    Args:
        db: The database session.
        ds_id: The primary key of the data source.

    Returns:
        The DataSource ORM object.

    Raises:
        HTTPException(404): If not found.
    """
    result = await db.execute(select(DataSource).where(DataSource.id == ds_id))
    ds = result.scalars().first()
    if ds is None:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return ds


async def get_all(db: AsyncSession) -> list[DataSource]:
    """List all data sources.

    Args:
        db: The database session.

    Returns:
        A list of DataSource ORM objects.
    """
    result = await db.execute(select(DataSource).order_by(DataSource.id))
    return list(result.scalars().all())


async def update(
    db: AsyncSession, ds_id: int, data: DataSourceUpdate
) -> DataSource:
    """Update an existing data source.

    Args:
        db: The database session.
        ds_id: The primary key of the data source.
        data: The partial update payload.

    Returns:
        The updated DataSource ORM object.
    """
    ds = await get(db, ds_id)
    update_data = data.model_dump(exclude_unset=True)

    # Encrypt password if provided
    if "password" in update_data and update_data["password"] is not None:
        update_data["password_encrypted"] = encrypt_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(ds, field, value)

    await db.commit()
    await db.refresh(ds)

    # Invalidate cached engine if host/port/user/password/database changed
    if ds_id in _engine_cache:
        await _dispose_engine(ds_id)

    logger.info("DataSource updated: id=%d", ds_id)
    return ds


async def delete(db: AsyncSession, ds_id: int) -> None:
    """Delete a data source record.
    For csv_temp sources, also drops the temp table.
    """
    ds = await get(db, ds_id)

    # Drop CSV temp table if applicable
    if ds.db_type == "csv_temp":
        try:
            from sqlalchemy import text as sa_text
            # Find the first table_metadata to get the table name
            result = await db.execute(
                select(TableMetadata.table_name).where(TableMetadata.datasource_id == ds_id)
            )
            table_name = result.scalars().first()
            if table_name:
                import aiomysql
                conn = await aiomysql.connect(
                    host=ds.host, port=ds.port,
                    user=ds.username, password=decrypt_password(ds.password_encrypted),
                    db=ds.database, autocommit=True,
                )
                cur = await conn.cursor()
                await cur.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                await cur.close()
                conn.close()
                logger.info("Dropped CSV temp table: %s", table_name)
        except Exception as exc:
            logger.warning("Failed to drop CSV temp table: %s", exc)

    await db.delete(ds)
    await db.commit()

    if ds_id in _engine_cache:
        await _dispose_engine(ds_id)

    logger.info("DataSource deleted: id=%d", ds_id)


async def test_connection(db: AsyncSession, ds_id: int) -> bool:
    """Test whether a data source connection is reachable.

    Delegates to the adapter registered for this datasource's ``db_type``.

    Args:
        db: The database session.
        ds_id: The primary key of the data source.

    Returns:
        ``True`` if the connection succeeded.
    """
    ds = await get(db, ds_id)
    password = decrypt_password(ds.password_encrypted)
    adapter = get_adapter(ds.db_type)
    params = _build_connection_params(ds, password)
    return await adapter.test_connection(params)


async def get_connection(db: AsyncSession, ds_id: int) -> AsyncEngine:
    """Get or create a dynamic SQLAlchemy async engine for a data source.

    Engines are cached by data source ID to avoid repeated creation.

    Args:
        db: The database session.
        ds_id: The primary key of the data source.

    Returns:
        A configured :class:`sqlalchemy.ext.asyncio.AsyncEngine`.
    """
    if ds_id in _engine_cache:
        return _engine_cache[ds_id]

    ds = await get(db, ds_id)
    password = decrypt_password(ds.password_encrypted)
    adapter = get_adapter(ds.db_type)
    params = _build_connection_params(ds, password)
    url = adapter.build_connection_url(params)
    engine = create_async_engine(
        url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=False,  # disabled: aiomysql's ping() signature is incompatible with SQLAlchemy's do_ping
        pool_recycle=1800,
    )
    _engine_cache[ds_id] = engine
    logger.info("Dynamic engine created for datasource id=%d type=%s", ds_id, ds.db_type)
    return engine


async def execute_query(
    db: AsyncSession, ds_id: int, sql: str
) -> list[dict]:
    """Execute a read-only SQL statement against a user data source.

    Args:
        db: The database session.
        ds_id: The primary key of the data source.
        sql: A validated, read-only SQL SELECT statement.

    Returns:
        A list of dicts, each representing one row.
    """
    engine = await get_connection(db, ds_id)
    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
        rows = result.fetchall()
        columns = list(result.keys())
        return [dict(zip(columns, row)) for row in rows]


async def _dispose_engine(ds_id: int) -> None:
    """Dispose and remove a cached dynamic engine."""
    engine = _engine_cache.pop(ds_id, None)
    if engine is not None:
        await engine.dispose()
        logger.info("Dynamic engine disposed for datasource id=%d", ds_id)


async def register_csv_datasource(
    db: AsyncSession,
    name: str,
    table_name: str,
) -> DataSource:
    """Register a CSV temp table as a data source.

    Args:
        db: The database session.
        name: Human-readable name for this CSV data source.
        table_name: The temp table name in lingwen_temp.

    Returns:
        The newly created DataSource ORM object.
    """
    ds = DataSource(
        name=name,
        db_type="csv_temp",
        host=settings.db_host,  # 从环境变量读取，Docker 中指向 mysql 服务
        port=3306,
        database="lingwen_temp",
        username="root",
        password_encrypted=encrypt_password("andy_l007"),
        status="active",
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    logger.info("CSV datasource registered: id=%d name=%s table=%s", ds.id, name, table_name)
    return ds
