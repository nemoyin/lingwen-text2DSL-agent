"""Apache Hive adapter.

Uses ``pyhive`` (synchronous) driver wrapped in ``asyncio.to_thread()``.
Schema introspection uses ``DESCRIBE`` or Hive metastore tables.
"""

import asyncio
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
class HiveAdapter(BaseDataSourceAdapter):
    """Adapter for Apache Hive 3.x via HiveServer2 (Thrift).

    ``pyhive`` is synchronous — ``test_connection`` uses ``asyncio.to_thread()``.
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

    def build_connection_url(self, params: ConnectionParams) -> str:
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        return f"hive+pyhive://{user}:{password}@{params.host}:{params.port}/{params.database}"

    async def test_connection(self, params: ConnectionParams) -> bool:
        def _sync_connect():
            try:
                from pyhive import hive
                conn = hive.Connection(
                    host=params.host, port=params.port,
                    username=params.username, password=params.password,
                    database=params.database,
                )
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

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=True)
        async with engine.connect() as conn:
            result = await conn.execute(text("SHOW TABLES IN {db}".format(db=params.database)))
            rows = result.fetchall()
        await engine.dispose()
        return [SchemaTable(table_name=r[0]) for r in rows]

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        tables = await self.scan_tables(params)
        columns: list[SchemaColumn] = []

        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=True)

        async with engine.connect() as conn:
            for tbl in tables:
                try:
                    result = await conn.execute(
                        text(f"DESCRIBE {tbl.table_name}")
                    )
                    rows = result.fetchall()
                    for i, r in enumerate(rows):
                        columns.append(SchemaColumn(
                            table_name=tbl.table_name,
                            column_name=r[0] if r[0] else "unknown",
                            data_type=r[1] if len(r) > 1 and r[1] else "string",
                            comment=r[2] if len(r) > 2 and r[2] else None,
                            ordinal_position=i + 1,
                        ))
                except Exception as exc:
                    logger.warning("Hive DESCRIBE failed for table %s: %s", tbl.table_name, exc)

        await engine.dispose()
        return columns

    def get_dialect_hint(self) -> str:
        return "HiveQL 查询。注意不支持行级 UPDATE/DELETE，分区裁剪优化(WHERE dt='...')，LATERAL VIEW EXPLODE 展开数组，不支持传统 JOIN 的 ON 条件中的非等值连接。"

    def get_extra_fields_schema(self) -> dict: return {}

    def uses_sqlalchemy(self) -> bool: return True
