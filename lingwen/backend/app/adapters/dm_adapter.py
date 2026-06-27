"""Dameng (DM8) database adapter.

Uses ``dmPython`` (synchronous) driver for connection testing and schema
introspection via ``asyncio.to_thread()``.  DM8 is Oracle-compatible at the
SQL level — schema queries use ``ALL_TABLES`` / ``ALL_TAB_COLUMNS``.

dmPython is sync-only, so scan methods use native client + to_thread.
Query execution uses DM's SQLAlchemy dialect ``dm+dmPython`` with the
sync→async fallback path (same as ClickHouse).
"""

import asyncio
import logging
from urllib.parse import quote_plus

from app.adapters import register_adapter
from app.adapters.base import (
    BaseDataSourceAdapter,
    ConnectionParams,
    SchemaColumn,
    SchemaTable,
)

logger = logging.getLogger(__name__)


@register_adapter
class DMAdapter(BaseDataSourceAdapter):
    """Adapter for Dameng DM8 (Oracle-compatible)."""

    @staticmethod
    def db_type() -> str: return "dm"
    @staticmethod
    def display_name() -> str: return "Dameng (DM8)"
    @staticmethod
    def default_port() -> int: return 5236
    @staticmethod
    def sqlalchemy_driver() -> str: return "dm+dmPython"

    # ── dmPython helper ───────────────────────────────────────────────────

    def _connect(self, params: ConnectionParams):
        """Create a synchronous dmPython connection."""
        import dmPython
        return dmPython.connect(
            server=params.host,
            port=params.port,
            user=params.username,
            password=params.password,
            autoCommit=True,
        )

    # ── Connection ───────────────────────────────────────────────────────

    def build_connection_url(self, params: ConnectionParams) -> str:
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        return (
            f"dm+dmPython://{user}:{password}"
            f"@{params.host}:{params.port}/{params.database}"
        )

    async def test_connection(self, params: ConnectionParams) -> bool:
        def _sync_test():
            try:
                conn = self._connect(params)
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchall()
                cursor.close()
                conn.close()
                return True
            except ImportError:
                logger.error("dmPython not installed")
                return False
            except Exception as exc:
                logger.warning("DM connection test failed: %s", exc)
                return False
        return await asyncio.to_thread(_sync_test)

    # ── Schema introspection (native dmPython — sync → to_thread) ────────

    def _owner(self, params: ConnectionParams) -> str:
        return params.username.upper()

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        owner = self._owner(params)

        def _sync():
            conn = self._connect(params)
            try:
                cursor = conn.cursor()
                # DM ALL_TABLES has no TABLE_TYPE column; filter by OWNER only
                cursor.execute(
                    f"SELECT TABLE_NAME FROM ALL_TABLES "
                    f"WHERE OWNER = '{owner}' "
                    f"ORDER BY TABLE_NAME"
                )
                rows = cursor.fetchall()
                cursor.close()
                return [SchemaTable(table_name=r[0]) for r in rows]
            finally:
                conn.close()

        return await asyncio.to_thread(_sync)

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        owner = self._owner(params)

        def _sync():
            conn = self._connect(params)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT "
                    f"  c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, "
                    f"  c.NULLABLE, c.DATA_DEFAULT, "
                    f"  cm.COMMENTS AS COL_COMMENT, "
                    f"  CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'PRI' ELSE '' END AS COL_KEY, "
                    f"  c.COLUMN_ID "
                    f"FROM ALL_TAB_COLUMNS c "
                    f"LEFT JOIN ALL_COL_COMMENTS cm "
                    f"  ON c.OWNER = cm.OWNER "
                    f"  AND c.TABLE_NAME = cm.TABLE_NAME "
                    f"  AND c.COLUMN_NAME = cm.COLUMN_NAME "
                    f"LEFT JOIN ("
                    f"  SELECT col.TABLE_NAME, col.COLUMN_NAME "
                    f"  FROM ALL_CONSTRAINTS cons, ALL_CONS_COLUMNS col "
                    f"  WHERE cons.OWNER = '{owner}' "
                    f"  AND cons.CONSTRAINT_TYPE = 'P' "
                    f"  AND cons.CONSTRAINT_NAME = col.CONSTRAINT_NAME "
                    f"  AND cons.OWNER = col.OWNER"
                    f") pk ON c.TABLE_NAME = pk.TABLE_NAME "
                    f"  AND c.COLUMN_NAME = pk.COLUMN_NAME "
                    f"WHERE c.OWNER = '{owner}' "
                    f"ORDER BY c.TABLE_NAME, c.COLUMN_ID"
                )
                rows = cursor.fetchall()
                cursor.close()
                return [
                    SchemaColumn(
                        table_name=r[0], column_name=r[1], data_type=r[2],
                        nullable=r[3] == "Y",
                        default_value=str(r[4]) if r[4] else None,
                        comment=r[5] if r[5] else None,
                        is_primary_key=r[6] == "PRI",
                        ordinal_position=int(r[7]) if r[7] else 0,
                    ) for r in rows
                ]
            finally:
                conn.close()

        return await asyncio.to_thread(_sync)

    # ── Dialect hint ─────────────────────────────────────────────────────

    def get_dialect_hint(self) -> str:
        return (
            "达梦 DM8 SQL 查询（兼容 Oracle 语法）。"
            "注意使用双引号标识符，ROWNUM 或 FETCH FIRST 分页，"
            "TO_DATE() 日期转换，NVL() 空值处理，"
            "支持 Oracle 兼容的分析函数和 CONNECT BY 递归。"
        )

    # ── Extra fields ─────────────────────────────────────────────────────

    def get_extra_fields_schema(self) -> dict: return {}

    # ── SQLAlchemy compatibility ─────────────────────────────────────────

    def uses_sqlalchemy(self) -> bool: return False

    # ── Query execution (native dmPython — sync → to_thread) ────────────

    async def execute_query(
        self, params: ConnectionParams, query: str
    ) -> list[dict]:
        """Execute a SQL query via native dmPython (sync → to_thread)."""
        import re as _re
        cleaned = query.strip().rstrip(";").strip()
        cleaned = _re.sub(r"```(?:\w+)?\s*$", "", cleaned).strip()

        def _sync_execute():
            conn = self._connect(params)
            try:
                cursor = conn.cursor()
                cursor.execute(cleaned)
                rows = cursor.fetchall()
                cols = (
                    [d[0] for d in cursor.description]
                    if cursor.description else []
                )
                cursor.close()
                return [dict(zip(cols, row)) for row in rows]
            finally:
                conn.close()

        return await asyncio.to_thread(_sync_execute)
