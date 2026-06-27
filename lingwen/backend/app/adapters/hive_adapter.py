"""Apache Hive adapter.

Uses ``pyhive`` (synchronous) driver wrapped in ``asyncio.to_thread()``
for both connection testing and schema introspection.  The ``hive+pyhive``
SQLAlchemy dialect does not support async, so scan and query execution use
native pyhive via ``to_thread``.
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
class HiveAdapter(BaseDataSourceAdapter):
    """Adapter for Apache Hive 3.x via HiveServer2 (Thrift).

    ``pyhive`` is synchronous — all operations use ``asyncio.to_thread()``.
    Schema introspection uses ``SHOW TABLES`` / ``DESCRIBE table``.
    """

    @staticmethod
    def db_type() -> str: return "hive"
    @staticmethod
    def display_name() -> str: return "Apache Hive"
    @staticmethod
    def default_port() -> int: return 10000
    @staticmethod
    def sqlalchemy_driver() -> str: return "hive+pyhive"

    # ── pyhive helper ─────────────────────────────────────────────────────

    def _connect(self, params: ConnectionParams):
        """Create a synchronous pyhive connection.

        The password field is required by the datasource schema but Hive
        in Docker defaults to NONE auth — always use ``auth='NONE'`` and
        never pass the password to pyhive.
        """
        from pyhive import hive
        return hive.Connection(
            host=params.host,
            port=params.port,
            username=params.username,
            database=params.database,
            auth="NONE",
        )

    # ── Connection ───────────────────────────────────────────────────────

    def build_connection_url(self, params: ConnectionParams) -> str:
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        return f"hive+pyhive://{user}:{password}@{params.host}:{params.port}/{params.database}"

    async def test_connection(self, params: ConnectionParams) -> bool:
        def _sync_connect():
            try:
                conn = self._connect(params)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()
                cursor.close()
                conn.close()
                return True
            except ImportError:
                logger.error("pyhive not installed")
                return False
            except Exception as exc:
                logger.warning("Hive connection test failed: %s", exc)
                return False

        return await asyncio.to_thread(_sync_connect)

    # ── Schema introspection (native pyhive — sync → to_thread) ──────────

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        def _sync_scan():
            conn = self._connect(params)
            try:
                cursor = conn.cursor()
                cursor.execute(f"SHOW TABLES IN {params.database}")
                rows = cursor.fetchall()
                cursor.close()
                return [SchemaTable(table_name=r[0]) for r in rows]
            finally:
                conn.close()

        return await asyncio.to_thread(_sync_scan)

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        tables = await self.scan_tables(params)
        columns: list[SchemaColumn] = []

        def _sync_describe(table_name: str) -> list[tuple]:
            conn = self._connect(params)
            try:
                cursor = conn.cursor()
                cursor.execute(f"DESCRIBE {table_name}")
                rows = cursor.fetchall()
                cursor.close()
                return rows
            finally:
                conn.close()

        for tbl in tables:
            try:
                rows = await asyncio.to_thread(_sync_describe, tbl.table_name)
                for i, r in enumerate(rows):
                    col_name = r[0].strip() if r[0] else "unknown"
                    # Skip partition info rows and separators
                    if col_name.startswith("#") or col_name == "":
                        continue
                    columns.append(SchemaColumn(
                        table_name=tbl.table_name,
                        column_name=col_name,
                        data_type=r[1].strip() if len(r) > 1 and r[1] else "string",
                        comment=r[2].strip() if len(r) > 2 and r[2] else None,
                        ordinal_position=i + 1,
                    ))
            except Exception as exc:
                logger.warning("Hive DESCRIBE failed for table %s: %s", tbl.table_name, exc)

        return columns

    # ── Dialect hint ─────────────────────────────────────────────────────

    def get_dialect_hint(self) -> str:
        return (
            "HiveQL 查询。注意不支持行级 UPDATE/DELETE，"
            "分区裁剪优化(WHERE dt='...')，LATERAL VIEW EXPLODE 展开数组，"
            "不支持传统 JOIN 的 ON 条件中的非等值连接，"
            "字符串类型字段比较时注意隐式类型转换。"
        )

    # ── Extra fields ─────────────────────────────────────────────────────

    def get_extra_fields_schema(self) -> dict: return {}

    # ── SQLAlchemy compatibility ──────────────────────────────────────────
    # hive+pyhive is sync-only — query execution falls back to sync engine
    # via datasource_service's async→sync fallback (same as ClickHouse).

    def uses_sqlalchemy(self) -> bool: return False

    # ── Query execution (native pyhive — sync → to_thread) ──────────────

    async def execute_query(
        self, params: ConnectionParams, query: str
    ) -> list[dict]:
        """Execute a HiveQL query via native pyhive (sync → to_thread)."""
        import re as _re
        cleaned = query.strip().rstrip(";").strip()
        cleaned = _re.sub(r"```(?:\w+)?\s*$", "", cleaned).strip()

        def _sync_execute():
            conn = self._connect(params)
            try:
                cursor = conn.cursor()
                cursor.execute(cleaned)
                rows = cursor.fetchall()
                # Get column names from cursor description
                cols = (
                    [d[0].split(".")[-1] for d in cursor.description]
                    if cursor.description else []
                )
                cursor.close()
                return [dict(zip(cols, row)) for row in rows]
            finally:
                conn.close()

        import asyncio as _asyncio
        return await _asyncio.to_thread(_sync_execute)
