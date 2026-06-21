"""Elasticsearch adapter.

Uses the ``elasticsearch-py`` async client.  Does NOT use SQLAlchemy —
schema introspection uses the REST API (``_cat/indices``, ``_mapping``).
Query language: ES|QL (Elasticsearch Query Language).
"""

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
class ElasticsearchAdapter(BaseDataSourceAdapter):
    """Adapter for Elasticsearch 8.x.

    Key differences from SQL-based adapters:
    - ``sqlalchemy_driver()`` returns ``""`` (no SQLAlchemy)
    - ``uses_sqlalchemy()`` returns ``False``
    - Schema = indices and their field mappings
    - ``get_dialect_hint()`` describes ES|QL syntax
    """

    @staticmethod
    def db_type() -> str: return "elasticsearch"
    @staticmethod
    def display_name() -> str: return "Elasticsearch"
    @staticmethod
    def default_port() -> int: return 9200
    @staticmethod
    def sqlalchemy_driver() -> str: return ""

    def _build_http_base(self, params: ConnectionParams) -> str:
        """Build the HTTP base URL for ES REST API calls."""
        secure = params.extra_params.get("secure", False)
        protocol = "https" if secure else "http"
        user = quote_plus(params.username)
        pw = quote_plus(params.password)
        return f"{protocol}://{user}:{pw}@{params.host}:{params.port}"

    def build_connection_url(self, params: ConnectionParams) -> str:
        """Return a canonical URL string (used as engine cache key, not for SQLAlchemy)."""
        return self._build_http_base(params)

    async def test_connection(self, params: ConnectionParams) -> bool:
        try:
            from elasticsearch import AsyncElasticsearch
            es = AsyncElasticsearch(
                [self._build_http_base(params)],
                verify_certs=params.extra_params.get("verify_certs", True),
                request_timeout=5,
            )
            ok = await es.ping()
            await es.close()
            return bool(ok)
        except ImportError:
            logger.error("elasticsearch-py not installed")
            return False
        except Exception as exc:
            logger.warning("Elasticsearch connection test failed: %s", exc)
            return False

    async def _es_client(self, params: ConnectionParams):
        """Return an authenticated AsyncElasticsearch client."""
        from elasticsearch import AsyncElasticsearch
        return AsyncElasticsearch(
            [self._build_http_base(params)],
            verify_certs=params.extra_params.get("verify_certs", True),
            request_timeout=10,
        )

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        es = await self._es_client(params)
        try:
            resp = await es.cat.indices(format="json", h="index,status,docs.count")
            await es.close()
            return [
                SchemaTable(
                    table_name=r.get("index", ""),
                    row_count_estimate=int(r.get("docs.count", 0)) if r.get("docs.count") else None,
                )
                for r in resp
                if not str(r.get("index", "")).startswith(".")  # skip system indices
            ]
        except Exception as exc:
            logger.warning("ES indices scan failed: %s", exc)
            await es.close()
            return []

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        tables = await self.scan_tables(params)
        columns: list[SchemaColumn] = []
        es = await self._es_client(params)

        for tbl in tables:
            try:
                resp = await es.indices.get_mapping(index=tbl.table_name)
                await es.close()

                index_data = resp.get(tbl.table_name, {})
                mappings = index_data.get("mappings", {})
                properties = mappings.get("properties", {})

                for i, (field_name, field_def) in enumerate(properties.items()):
                    columns.append(SchemaColumn(
                        table_name=tbl.table_name,
                        column_name=field_name,
                        data_type=field_def.get("type", "unknown"),
                        nullable=True,
                        ordinal_position=i + 1,
                    ))
            except Exception as exc:
                logger.warning("ES mapping scan failed for index %s: %s", tbl.table_name, exc)

        return columns

    def get_dialect_hint(self) -> str:
        return (
            "ES|QL (Elasticsearch Query Language) 查询。"
            "注意使用管道式语法 `|` 分隔命令，FROM 指定索引名，"
            "dot-path 访问嵌套字段(obj.field)，"
            "不支持传统 SQL JOIN，使用 ENRICH 策略替代。"
        )

    def get_extra_fields_schema(self) -> dict:
        return {
            "auth_type": {
                "type": "string",
                "enum": ["basic", "api_key", "cloud"],
                "default": "basic",
                "label": "认证方式",
            },
            "api_key": {"type": "string", "label": "API Key (base64)", "description": "使用 api_key 认证时必填"},
            "cloud_id": {"type": "string", "label": "Cloud ID", "description": "Elastic Cloud 部署 ID"},
            "secure": {"type": "boolean", "default": False, "label": "HTTPS"},
            "verify_certs": {"type": "boolean", "default": True, "label": "验证 SSL 证书"},
        }

    def uses_sqlalchemy(self) -> bool: return False
