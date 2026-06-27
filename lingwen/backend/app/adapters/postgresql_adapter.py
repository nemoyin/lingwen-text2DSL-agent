"""PostgreSQL database adapter.

Requires ``asyncpg`` (``pip install asyncpg``) for connection testing.
"""

import logging
from urllib.parse import quote_plus

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
class PostgreSQLAdapter(BaseDataSourceAdapter):
    """Adapter for PostgreSQL 12+ data sources.

    Connection uses ``asyncpg`` via the ``postgresql+asyncpg`` SQLAlchemy
    dialect.  Schema introspection queries ``information_schema`` with
    ``table_schema`` filtering.
    """

    # ── Static identity ──────────────────────────────────────────────────

    @staticmethod
    def db_type() -> str:
        return "postgresql"

    @staticmethod
    def display_name() -> str:
        return "PostgreSQL"

    @staticmethod
    def default_port() -> int:
        return 5432

    @staticmethod
    def sqlalchemy_driver() -> str:
        return "postgresql+asyncpg"

    # ── Connection ───────────────────────────────────────────────────────

    def build_connection_url(self, params: ConnectionParams) -> str:
        """Build a ``postgresql+asyncpg://`` URL.

        The ``schema`` extra_param is used at query time by schema-scanning
        methods; search_path is NOT forced via ``options=`` because asyncpg
        does not accept that parameter (unlike psycopg2).
        """
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        host = params.host
        port = params.port
        database = params.database
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{host}:{port}/{database}"
        )

    async def test_connection(self, params: ConnectionParams) -> bool:
        """Open a short-lived asyncpg connection and execute SELECT 1."""
        try:
            import asyncpg  # lazy import — adapter registers without driver
            conn = await asyncpg.connect(
                host=params.host,
                port=params.port,
                user=params.username,
                password=params.password,
                database=params.database,
                timeout=5,
            )
            await conn.execute("SELECT 1")
            await conn.close()
            logger.info("PostgreSQL connection test passed: %s:%d", params.host, params.port)
            return True
        except ImportError:
            logger.error("asyncpg not installed — cannot test PostgreSQL connection")
            return False
        except Exception as exc:
            logger.warning(
                "PostgreSQL connection test failed: %s:%d error=%s",
                params.host, params.port, exc,
            )
            return False

    # ── Schema introspection ─────────────────────────────────────────────

    def _schema_name(self, params: ConnectionParams) -> str:
        """Return the schema name to introspect (default: 'public')."""
        return params.extra_params.get("schema", "public")

    async def scan_tables(
        self, params: ConnectionParams
    ) -> list[SchemaTable]:
        """Query ``information_schema.TABLES`` for PostgreSQL."""
        schema = self._schema_name(params)
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=False)

        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT table_name, "
                    "       pg_catalog.obj_description(pgc.oid, 'pg_class') AS table_comment "
                    "FROM information_schema.tables t "
                    "JOIN pg_catalog.pg_class pgc ON t.table_name = pgc.relname "
                    "WHERE t.table_schema = :schema AND t.table_type = 'BASE TABLE'"
                ),
                {"schema": schema},
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
        """Query ``information_schema.COLUMNS`` for PostgreSQL.

        Primary-key detection uses ``information_schema.key_column_usage``
        via a LEFT JOIN.
        """
        schema = self._schema_name(params)
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=False)

        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT "
                    "  c.table_name, c.column_name, c.data_type, "
                    "  c.is_nullable, c.column_default, "
                    "  pg_catalog.col_description(pgc.oid, c.ordinal_position) AS col_comment, "
                    "  CASE WHEN kcu.column_name IS NOT NULL THEN 'PRI' ELSE '' END AS column_key, "
                    "  c.ordinal_position "
                    "FROM information_schema.columns c "
                    "JOIN pg_catalog.pg_class pgc ON c.table_name = pgc.relname "
                    "LEFT JOIN information_schema.table_constraints tc "
                    "  ON tc.table_schema = c.table_schema "
                    " AND tc.table_name = c.table_name "
                    " AND tc.constraint_type = 'PRIMARY KEY' "
                    "LEFT JOIN information_schema.key_column_usage kcu "
                    "  ON kcu.constraint_name = tc.constraint_name "
                    " AND kcu.table_schema = c.table_schema "
                    " AND kcu.table_name = c.table_name "
                    " AND kcu.column_name = c.column_name "
                    "WHERE c.table_schema = :schema "
                    "ORDER BY c.table_name, c.ordinal_position"
                ),
                {"schema": schema},
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
        return (
            "PostgreSQL SQL 查询。注意使用双引号(\")标识符，"
            "LIMIT/OFFSET 分页，::类型转换语法，"
            "支持 CTE (WITH 子句)，窗口函数，"
            "以及 PostgreSQL 特有的数据类型如 JSONB、ARRAY。"
        )

    # ── Extra fields ─────────────────────────────────────────────────────

    def get_extra_fields_schema(self) -> dict:
        return {
            "schema": {
                "type": "string",
                "default": "public",
                "label": "Schema",
                "description": "PostgreSQL schema name to introspect (default: public)",
            }
        }

    def validate_params(self, params: ConnectionParams) -> list[str]:
        errors = super().validate_params(params)
        if not params.database:
            errors.append("数据库名不能为空")
        return errors

    def uses_sqlalchemy(self) -> bool:
        return True
