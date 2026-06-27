"""Apache Doris database adapter.

Doris is MySQL-protocol compatible — reuses ``aiomysql`` driver and
``information_schema`` queries.  Key differences from MySQL: query port
defaults to 9030 (FE), aggregation model tables don't support DELETE/UPDATE.
"""

import logging
from urllib.parse import quote_plus

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
class DorisAdapter(BaseDataSourceAdapter):
    """Adapter for Apache Doris (MySQL-compatible wire protocol)."""

    @staticmethod
    def db_type() -> str: return "doris"

    @staticmethod
    def display_name() -> str: return "Apache Doris"

    @staticmethod
    def default_port() -> int: return 9030

    @staticmethod
    def sqlalchemy_driver() -> str: return "mysql+aiomysql"

    def build_connection_url(self, params: ConnectionParams) -> str:
        user = quote_plus(params.username)
        password = quote_plus(params.password)
        return f"mysql+aiomysql://{user}:{password}@{params.host}:{params.port}/{params.database}?charset=utf8mb4"

    async def test_connection(self, params: ConnectionParams) -> bool:
        try:
            conn = await aiomysql.connect(
                host=params.host, port=params.port, user=params.username,
                password=params.password, db=params.database, connect_timeout=5,
            )
            await conn.ping()
            conn.close()
            return True
        except Exception as exc:
            logger.warning("Doris connection test failed: %s", exc)
            return False

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=False)
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES WHERE TABLE_SCHEMA=:db AND TABLE_TYPE='BASE TABLE'"),
                {"db": params.database},
            )
            rows = result.fetchall()
        await engine.dispose()
        return [SchemaTable(table_name=r[0], table_comment=r[1] if r[1] else None) for r in rows]

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        url = self.build_connection_url(params)
        engine = create_async_engine(url, echo=False, pool_pre_ping=False)
        async with engine.connect() as conn:
            result = await conn.execute(
                text("SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE,COLUMN_DEFAULT,COLUMN_COMMENT,COLUMN_KEY,ORDINAL_POSITION FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=:db ORDER BY TABLE_NAME,ORDINAL_POSITION"),
                {"db": params.database},
            )
            rows = result.fetchall()
        await engine.dispose()
        return [SchemaColumn(table_name=r[0], column_name=r[1], data_type=r[2], nullable=r[3]=="YES", default_value=str(r[4]) if r[4] is not None else None, comment=r[5] if r[5] else None, is_primary_key=r[6]=="PRI", ordinal_position=int(r[7]) if r[7] else 0) for r in rows]

    def get_dialect_hint(self) -> str:
        return (
            "Apache Doris SQL 查询（兼容 MySQL 协议）。"
            "注意：标识符不要使用反引号(`)，使用双引号或直接引用。"
            "聚合模型表不可直接 DELETE/UPDATE，"
            "使用 BITMAP/HLL 近似去重，支持特有的聚合函数。"
        )

    def get_extra_fields_schema(self) -> dict: return {}

    def uses_sqlalchemy(self) -> bool: return True
