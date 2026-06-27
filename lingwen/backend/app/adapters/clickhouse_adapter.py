"""ClickHouse database adapter.

Uses ``clickhouse-connect`` (sync) for connection testing and schema
introspection.  The SQLAlchemy dialect ``clickhouse+http`` is **sync-only**
(no async driver exists), so schema scanning uses the native client wrapped
in ``asyncio.to_thread()``.
"""

import asyncio
import logging
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
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
class ClickHouseAdapter(BaseDataSourceAdapter):
    """Adapter for ClickHouse 22+.

    Schema introspection uses ``system.tables`` and ``system.columns``
    via the native ``clickhouse-connect`` client (sync → to_thread).
    The ``secure`` extra_param toggles HTTPS (port 8443).
    """

    @staticmethod
    def db_type() -> str: return "clickhouse"
    @staticmethod
    def display_name() -> str: return "ClickHouse"
    @staticmethod
    def default_port() -> int: return 8123
    @staticmethod
    def sqlalchemy_driver() -> str: return "clickhouse+http"

    # ── Connection ───────────────────────────────────────────────────────

    def build_connection_url(self, params: ConnectionParams) -> str:
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        protocol = "https" if params.extra_params.get("secure") else "http"
        return f"clickhouse+{protocol}://{user}:{password}@{params.host}:{params.port}/{params.database}"

    async def test_connection(self, params: ConnectionParams) -> bool:
        try:
            import clickhouse_connect  # lazy import
            client = clickhouse_connect.get_client(
                host=params.host, port=params.port,
                username=params.username, password=params.password,
                database=params.database, connect_timeout=5,
            )
            client.command("SELECT 1")
            client.close()
            return True
        except ImportError:
            logger.error("clickhouse-connect not installed")
            return False
        except Exception as exc:
            logger.warning("ClickHouse connection test failed: %s", exc)
            return False

    # ── Schema introspection (native client — sync driver has no async) ──

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        """Query ``system.tables`` via native client (sync → to_thread)."""

        def _sync_scan():
            import clickhouse_connect
            client = clickhouse_connect.get_client(
                host=params.host, port=params.port,
                username=params.username, password=params.password,
                database=params.database, connect_timeout=10,
            )
            try:
                rows = client.query(
                    "SELECT name, comment FROM system.tables "
                    "WHERE database = {db:String} AND engine NOT IN ('Distributed')",
                    parameters={"db": params.database},
                ).result_rows
                return [
                    SchemaTable(
                        table_name=r[0],
                        table_comment=r[1] if r[1] else None,
                    )
                    for r in rows
                ]
            finally:
                client.close()

        return await asyncio.to_thread(_sync_scan)

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        """Query ``system.columns`` via native client (sync → to_thread)."""

        def _sync_scan():
            import clickhouse_connect
            client = clickhouse_connect.get_client(
                host=params.host, port=params.port,
                username=params.username, password=params.password,
                database=params.database, connect_timeout=10,
            )
            try:
                rows = client.query(
                    "SELECT table, name, type, comment, is_in_primary_key, position "
                    "FROM system.columns WHERE database = {db:String} "
                    "ORDER BY table, position",
                    parameters={"db": params.database},
                ).result_rows
                return [
                    SchemaColumn(
                        table_name=r[0], column_name=r[1], data_type=r[2],
                        nullable=True,
                        comment=r[3] if r[3] else None,
                        is_primary_key=bool(r[4]) if r[4] else False,
                        ordinal_position=int(r[5]) if r[5] else 0,
                    ) for r in rows
                ]
            finally:
                client.close()

        return await asyncio.to_thread(_sync_scan)

    # ── Dialect hint ─────────────────────────────────────────────────────

    def get_dialect_hint(self) -> str:
        return (
            "ClickHouse SQL 查询。注意使用 FINAL 修饰符，ArrayJoin 展开数组，"
            "特有的聚合函数组合器(-If/-Array/-Merge)，LIMIT n BY 语法，"
            "不可直接 DELETE/UPDATE 行级数据。"
        )

    # ── Extra fields ─────────────────────────────────────────────────────

    def get_extra_fields_schema(self) -> dict:
        return {
            "secure": {
                "type": "boolean", "default": False,
                "label": "HTTPS", "description": "Use HTTPS (port 8443)",
            },
        }

    # ── SQLAlchemy compatibility ──────────────────────────────────────────
    # clickhouse+http is sync-only — get_connection() in datasource_service
    # falls back to a sync engine wrapped in asyncio.to_thread().

    def uses_sqlalchemy(self) -> bool: return True
