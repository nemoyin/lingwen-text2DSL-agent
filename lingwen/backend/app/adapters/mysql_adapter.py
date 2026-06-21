"""MySQL database adapter.

Extracted from ``datasource_service.py`` and ``schema_service.py``.
This adapter encapsulates all MySQL-specific connection, introspection, and
dialect logic.  It is the reference implementation for the adapter pattern.
"""

import logging
from urllib.parse import quote_plus
from typing import Optional

import aiomysql
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.adapters import register_adapter
from app.adapters.base import (
    BaseDataSourceAdapter,
    ConnectionParams,
    SchemaColumn,
    SchemaTable,
)

logger = logging.getLogger(__name__)


@register_adapter
class MySQLAdapter(BaseDataSourceAdapter):
    """Adapter for MySQL 5.7 / 8.0 data sources.

    Connection uses ``aiomysql`` (async) via the ``mysql+aiomysql`` SQLAlchemy
    dialect.  Schema introspection reads ``information_schema``.
    """

    # ── Static identity ──────────────────────────────────────────────────

    @staticmethod
    def db_type() -> str:
        return "mysql"

    @staticmethod
    def display_name() -> str:
        return "MySQL"

    @staticmethod
    def default_port() -> int:
        return 3306

    @staticmethod
    def sqlalchemy_driver() -> str:
        return "mysql+aiomysql"

    # ── Connection ───────────────────────────────────────────────────────

    def build_connection_url(self, params: ConnectionParams) -> str:
        """Build a ``mysql+aiomysql://`` URL with charset=utf8mb4."""
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        host = params.host
        port = params.port
        database = params.database
        return (
            f"mysql+aiomysql://{user}:{password}"
            f"@{host}:{port}/{database}?charset=utf8mb4"
        )

    async def test_connection(self, params: ConnectionParams) -> bool:
        """Open a short-lived ``aiomysql`` connection and ping."""
        try:
            conn = await aiomysql.connect(
                host=params.host,
                port=params.port,
                user=params.username,
                password=params.password,
                db=params.database,
                connect_timeout=5,
            )
            await conn.ping()
            conn.close()
            logger.info("MySQL connection test passed: %s:%d", params.host, params.port)
            return True
        except Exception as exc:
            logger.warning(
                "MySQL connection test failed: %s:%d error=%s",
                params.host, params.port, exc,
            )
            return False

    # ── Schema introspection ─────────────────────────────────────────────

    async def scan_tables(
        self, params: ConnectionParams
    ) -> list[SchemaTable]:
        """Query ``information_schema.TABLES`` for user tables."""
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=False)

        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT TABLE_NAME, TABLE_COMMENT "
                    "FROM information_schema.TABLES "
                    "WHERE TABLE_SCHEMA = :db AND TABLE_TYPE = 'BASE TABLE'"
                ),
                {"db": params.database},
            )
            rows = result.fetchall()

        await engine.dispose()

        return [
            SchemaTable(
                table_name=row[0],
                table_comment=row[1] if row[1] else None,
            )
            for row in rows
        ]

    async def scan_columns(
        self, params: ConnectionParams
    ) -> list[SchemaColumn]:
        """Query ``information_schema.COLUMNS`` for all columns.

        Primary key detection uses ``COLUMN_KEY = 'PRI'`` (MySQL-specific).
        """
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=False)

        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT "
                    "  TABLE_NAME, COLUMN_NAME, DATA_TYPE, "
                    "  IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT, "
                    "  COLUMN_KEY, ORDINAL_POSITION "
                    "FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = :db "
                    "ORDER BY TABLE_NAME, ORDINAL_POSITION"
                ),
                {"db": params.database},
            )
            rows = result.fetchall()

        await engine.dispose()

        return [
            SchemaColumn(
                table_name=row[0],
                column_name=row[1],
                data_type=row[2],
                nullable=row[3] == "YES",
                default_value=str(row[4]) if row[4] is not None else None,
                comment=row[5] if row[5] else None,
                is_primary_key=row[6] == "PRI",
                ordinal_position=int(row[7]) if row[7] else 0,
            )
            for row in rows
        ]

    # ── Dialect hint ─────────────────────────────────────────────────────

    def get_dialect_hint(self) -> str:
        """Return MySQL-specific SQL generation guidance."""
        return (
            "MySQL SQL 查询。注意使用反引号(`)标识符，"
            "LIMIT 分页，NOW() 获取当前时间，"
            "DATE_FORMAT() 格式化日期。"
        )

    # ── Extra fields ─────────────────────────────────────────────────────

    def get_extra_fields_schema(self) -> dict:
        """MySQL has no type-specific extra connection fields."""
        return {}

    # ── Optional: whether this adapter uses SQLAlchemy ───────────────────

    def uses_sqlalchemy(self) -> bool:
        """MySQL queries are executed via SQLAlchemy ``text()``."""
        return True
