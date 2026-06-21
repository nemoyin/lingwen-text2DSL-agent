"""Oracle database adapter.

Uses ``oracledb`` (python-oracledb) in thin mode — no Oracle Instant Client needed.
Introspects ``ALL_TABLES`` / ``ALL_TAB_COLUMNS`` / ``ALL_TAB_COMMENTS``.
Requires ``service_name`` or ``sid`` in extra_params.
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
class OracleAdapter(BaseDataSourceAdapter):
    """Adapter for Oracle 12c+ (thin mode via python-oracledb)."""

    @staticmethod
    def db_type() -> str: return "oracle"
    @staticmethod
    def display_name() -> str: return "Oracle"
    @staticmethod
    def default_port() -> int: return 1521
    @staticmethod
    def sqlalchemy_driver() -> str: return "oracle+oracledb"

    def build_connection_url(self, params: ConnectionParams) -> str:
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        base = f"oracle+oracledb://{user}:{password}@{params.host}:{params.port}/"
        svc = params.extra_params.get("service_name")
        sid = params.extra_params.get("sid")
        if svc:
            return base + f"?service_name={quote_plus(svc)}"
        if sid:
            return base + f"?sid={quote_plus(sid)}"
        return base + params.database

    async def test_connection(self, params: ConnectionParams) -> bool:
        try:
            import oracledb  # lazy import
            dsn = oracledb.connect_params(
                host=params.host, port=params.port,
                service_name=params.extra_params.get("service_name", params.database),
                user=params.username, password=params.password,
            )
            conn = await oracledb.connect_async(params=dsn, timeout=5)
            await conn.ping()
            await conn.close()
            return True
        except ImportError:
            logger.error("oracledb not installed")
            return False
        except Exception as exc:
            logger.warning("Oracle connection test failed: %s", exc)
            return False

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        owner = params.username.upper()
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT TABLE_NAME, COMMENTS FROM ALL_TAB_COMMENTS WHERE OWNER=:owner AND TABLE_TYPE='TABLE' ORDER BY TABLE_NAME"),
                {"owner": owner},
            )
            rows = result.fetchall()
        await engine.dispose()
        return [SchemaTable(table_name=r[0], table_comment=r[1] if r[1] else None) for r in rows]

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        owner = params.username.upper()
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        async with engine.connect() as conn:
            # PK detection via ALL_CONSTRAINTS / ALL_CONS_COLUMNS
            result = await conn.execute(
                text(
                    "SELECT c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.NULLABLE, c.DATA_DEFAULT, "
                    "       cc.COMMENTS, "
                    "       CASE WHEN pk.column_name IS NOT NULL THEN 'PRI' ELSE '' END AS COLUMN_KEY, "
                    "       c.COLUMN_ID "
                    "FROM ALL_TAB_COLUMNS c "
                    "LEFT JOIN ALL_COL_COMMENTS cc ON c.OWNER=cc.OWNER AND c.TABLE_NAME=cc.TABLE_NAME AND c.COLUMN_NAME=cc.COLUMN_NAME "
                    "LEFT JOIN ("
                    "  SELECT cols.table_name, cols.column_name "
                    "  FROM ALL_CONSTRAINTS cons, ALL_CONS_COLUMNS cols "
                    "  WHERE cons.OWNER=:owner AND cons.CONSTRAINT_TYPE='P' "
                    "  AND cons.CONSTRAINT_NAME=cols.CONSTRAINT_NAME AND cons.OWNER=cols.OWNER"
                    ") pk ON c.TABLE_NAME=pk.table_name AND c.COLUMN_NAME=pk.column_name "
                    "WHERE c.OWNER=:owner "
                    "ORDER BY c.TABLE_NAME, c.COLUMN_ID"
                ),
                {"owner": owner},
            )
            rows = result.fetchall()
        await engine.dispose()
        return [
            SchemaColumn(
                table_name=r[0], column_name=r[1], data_type=r[2],
                nullable=r[3] == "Y", default_value=str(r[4]) if r[4] is not None else None,
                comment=r[5] if r[5] else None, is_primary_key=r[6] == "PRI",
                ordinal_position=int(r[7]) if r[7] else 0,
            ) for r in rows
        ]

    def get_dialect_hint(self) -> str:
        return "Oracle SQL 查询。注意使用双引号标识符，ROWNUM 或 FETCH FIRST 分页，TO_DATE() 日期转换，NVL() 空值处理，Oracle 特有的分析函数。"

    def get_extra_fields_schema(self) -> dict:
        return {
            "service_name": {"type": "string", "label": "Service Name", "description": "Oracle service name (recommended)"},
            "sid": {"type": "string", "label": "SID", "description": "Oracle SID (alternative to service name)"},
        }

    def validate_params(self, params: ConnectionParams) -> list[str]:
        errors = super().validate_params(params)
        if not params.extra_params.get("service_name") and not params.extra_params.get("sid"):
            errors.append("Oracle 需要指定 service_name 或 sid")
        return errors

    def uses_sqlalchemy(self) -> bool: return True
