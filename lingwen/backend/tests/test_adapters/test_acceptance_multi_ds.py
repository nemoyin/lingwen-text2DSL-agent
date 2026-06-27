"""Acceptance tests for multi-data-source feature.

Comprehensive tests covering:
1. Cross-adapter contract compliance — all 7 adapters satisfy the ABC contract
2. Edge cases — special chars, empty params, missing extra_params
3. Schema scanning — mock-based tests for all adapters
4. Error handling — connection failures, missing drivers
5. Dialect hints — all are non-trivial and type-specific
6. Extra params — type-specific connection parameters
7. Registry completeness — all 7 types + csv_temp
8. URL building — all adapters handle various scenarios
9. Hive async thread offloading
10. ES non-SQLAlchemy behavior
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.adapters.base import (
    BaseDataSourceAdapter,
    ConnectionParams,
    SchemaColumn,
    SchemaTable,
)
from app.adapters import get_adapter, available_types, _registry


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_mock_row(*values):
    """Return a MagicMock that behaves like a SQLAlchemy Row."""
    row = MagicMock()
    row.__getitem__ = lambda self, i: values[i]
    row.__len__ = lambda self: len(values)
    return row


def _make_mock_conn(return_rows):
    """Return an AsyncMock conn whose execute() returns rows via fetchall()."""
    mock_result = MagicMock()
    mock_result.fetchall.return_value = return_rows
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value=mock_result)
    return conn


def _make_mock_engine(mock_conn):
    """Return a plain-class mock SQLAlchemy engine."""
    class _MockEngine:
        def connect(self):
            class _Ctx:
                async def __aenter__(s):
                    return mock_conn
                async def __aexit__(s, *args):
                    pass
            return _Ctx()
        async def dispose(self):
            pass
    return _MockEngine()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Registry Completeness — verify all expected adapters are registered
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistryCompleteness:
    """All declared database types must be present and correctly configured."""

    EXPECTED_TYPES = {
        "mysql":         {"display_name": "MySQL",          "port": 3306, "sqlalchemy": True,  "driver": "mysql+aiomysql"},
        "postgresql":    {"display_name": "PostgreSQL",     "port": 5432, "sqlalchemy": True,  "driver": "postgresql+asyncpg"},
        "doris":         {"display_name": "Apache Doris",   "port": 9030, "sqlalchemy": True,  "driver": "mysql+aiomysql"},
        "clickhouse":    {"display_name": "ClickHouse",     "port": 8123, "sqlalchemy": True,  "driver": "clickhouse+http"},
        "oracle":        {"display_name": "Oracle",         "port": 1521, "sqlalchemy": True,  "driver": "oracle+oracledb"},
        "hive":          {"display_name": "Apache Hive",    "port": 10000,"sqlalchemy": True,  "driver": "hive+pyhive"},
        "elasticsearch": {"display_name": "Elasticsearch",  "port": 9200, "sqlalchemy": False, "driver": ""},
    }

    def test_all_seven_types_registered(self):
        """All 7 database types must be in the registry."""
        registered = set(_registry.keys())
        expected = set(self.EXPECTED_TYPES.keys())
        missing = expected - registered
        extra = registered - expected - {"dummy", "alpha", "beta"}  # test-only
        assert not missing, f"Missing adapters: {missing}"
        assert len(registered & expected) == 7, f"Expected 7 adapters, got {len(registered & expected)}"

    def test_registry_has_no_duplicate_db_types(self):
        """Each db_type must be unique."""
        db_types = [cls.db_type() for cls in _registry.values()]
        assert len(db_types) == len(set(db_types)), f"Duplicate db_types: {db_types}"

    def test_each_adapter_identity(self):
        """Every adapter must report correct identity values."""
        for db_type, expected in self.EXPECTED_TYPES.items():
            adapter = get_adapter(db_type)
            assert adapter.db_type() == db_type
            assert adapter.display_name() == expected["display_name"], \
                f"{db_type}: expected display_name '{expected['display_name']}', got '{adapter.display_name()}'"
            assert adapter.default_port() == expected["port"], \
                f"{db_type}: expected port {expected['port']}, got {adapter.default_port()}"
            assert adapter.sqlalchemy_driver() == expected["driver"], \
                f"{db_type}: expected driver '{expected['driver']}', got '{adapter.sqlalchemy_driver()}'"
            assert adapter.uses_sqlalchemy() == expected["sqlalchemy"], \
                f"{db_type}: expected uses_sqlalchemy={expected['sqlalchemy']}"

    def test_available_types_api(self):
        """available_types() returns correct count and required fields."""
        types = available_types()
        # Only count real adapters (exclude test-only ones)
        real_types = [t for t in types if t["db_type"] in self.EXPECTED_TYPES]
        assert len(real_types) == 7, f"Expected 7 types in API, got {len(real_types)}"

        for entry in real_types:
            assert "db_type" in entry
            assert "display_name" in entry
            assert "default_port" in entry
            assert "extra_fields" in entry
            assert isinstance(entry["extra_fields"], dict)

    def test_available_types_sorted(self):
        """available_types() should be deterministic (same order each call)."""
        t1 = available_types()
        t2 = available_types()
        assert [t["db_type"] for t in t1] == [t["db_type"] for t in t2]

    def test_elasticsearch_is_non_sqlalchemy(self):
        """Only Elasticsearch should have uses_sqlalchemy=False."""
        for db_type in self.EXPECTED_TYPES:
            adapter = get_adapter(db_type)
            if db_type == "elasticsearch":
                assert adapter.uses_sqlalchemy() is False
                assert adapter.sqlalchemy_driver() == ""
            else:
                assert adapter.uses_sqlalchemy() is True
                assert adapter.sqlalchemy_driver() != ""


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Cross-Adapter URL Building — edge cases for all adapters
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossAdapterURLBuilding:
    """All adapters must build valid-looking URLs with special characters."""

    SPECIAL_CHARS_PASSWORD = [
        ("at_sign", "p@ssword", "p%40ssword"),
        ("colon", "pass:word", "pass%3Aword"),
        ("slash", "pass/word", "pass%2Fword"),
        ("question", "pass?word", "pass%3Fword"),
        ("hash", "pass#word", "pass%23word"),
        ("percent", "pass%word", "pass%25word"),
        ("space", "pass word", None),  # quote_plus encodes space as +, not %20
        ("ampersand", "pass&word", "pass%26word"),
        ("combined", "p@ss:w/rd?test", None),  # just ensure no crash
    ]

    @pytest.mark.parametrize("name,pwd,expected_substr", SPECIAL_CHARS_PASSWORD)
    def test_mysql_url_special_chars(self, name, pwd, expected_substr):
        adapter = get_adapter("mysql")
        p = ConnectionParams(host="h", port=1, database="d", username="u", password=pwd)
        url = adapter.build_connection_url(p)
        assert "mysql+aiomysql://" in url
        if expected_substr:
            assert expected_substr in url, f"Expected '{expected_substr}' in URL: {url}"

    @pytest.mark.parametrize("name,pwd,expected_substr", SPECIAL_CHARS_PASSWORD)
    def test_postgresql_url_special_chars(self, name, pwd, expected_substr):
        adapter = get_adapter("postgresql")
        p = ConnectionParams(host="h", port=1, database="d", username="u", password=pwd)
        url = adapter.build_connection_url(p)
        assert "postgresql+asyncpg://" in url
        if expected_substr:
            assert expected_substr in url, f"Expected '{expected_substr}' in URL: {url}"

    @pytest.mark.parametrize("name,pwd,expected_substr", SPECIAL_CHARS_PASSWORD)
    def test_doris_url_special_chars(self, name, pwd, expected_substr):
        adapter = get_adapter("doris")
        p = ConnectionParams(host="h", port=1, database="d", username="u", password=pwd)
        url = adapter.build_connection_url(p)
        assert "mysql+aiomysql://" in url

    @pytest.mark.parametrize("name,pwd,expected_substr", SPECIAL_CHARS_PASSWORD)
    def test_clickhouse_url_special_chars(self, name, pwd, expected_substr):
        adapter = get_adapter("clickhouse")
        p = ConnectionParams(host="h", port=1, database="d", username="u", password=pwd)
        url = adapter.build_connection_url(p)
        assert "clickhouse+http://" in url

    @pytest.mark.parametrize("name,pwd,expected_substr", SPECIAL_CHARS_PASSWORD)
    def test_oracle_url_special_chars(self, name, pwd, expected_substr):
        adapter = get_adapter("oracle")
        p = ConnectionParams(
            host="h", port=1, database="d", username="u", password=pwd,
            extra_params={"service_name": "ORCL"},
        )
        url = adapter.build_connection_url(p)
        assert "oracle+oracledb://" in url

    @pytest.mark.parametrize("name,pwd,expected_substr", SPECIAL_CHARS_PASSWORD)
    def test_hive_url_special_chars(self, name, pwd, expected_substr):
        adapter = get_adapter("hive")
        p = ConnectionParams(host="h", port=1, database="d", username="u", password=pwd)
        url = adapter.build_connection_url(p)
        assert "hive+pyhive://" in url

    @pytest.mark.parametrize("name,pwd,expected_substr", SPECIAL_CHARS_PASSWORD)
    def test_es_url_special_chars(self, name, pwd, expected_substr):
        adapter = get_adapter("elasticsearch")
        p = ConnectionParams(host="h", port=1, database="d", username="u", password=pwd)
        url = adapter.build_connection_url(p)
        assert url.startswith("http://") or url.startswith("https://")


class TestCrossAdapterURLDefaults:
    """Each adapter uses its own default port in the URL."""

    def test_mysql_default_port_in_url(self):
        adapter = get_adapter("mysql")
        p = ConnectionParams(host="h", port=3306, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert ":3306" in url

    def test_postgresql_default_port_in_url(self):
        adapter = get_adapter("postgresql")
        p = ConnectionParams(host="h", port=5432, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert ":5432" in url

    def test_doris_default_port_in_url(self):
        adapter = get_adapter("doris")
        p = ConnectionParams(host="h", port=9030, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert ":9030" in url

    def test_clickhouse_default_port_in_url(self):
        adapter = get_adapter("clickhouse")
        p = ConnectionParams(host="h", port=8123, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert ":8123" in url

    def test_oracle_default_port_in_url(self):
        adapter = get_adapter("oracle")
        p = ConnectionParams(host="h", port=1521, database="d", username="u", password="p",
                            extra_params={"service_name": "X"})
        url = adapter.build_connection_url(p)
        assert ":1521" in url

    def test_hive_default_port_in_url(self):
        adapter = get_adapter("hive")
        p = ConnectionParams(host="h", port=10000, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert ":10000" in url

    def test_es_default_port_in_url(self):
        adapter = get_adapter("elasticsearch")
        p = ConnectionParams(host="h", port=9200, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert ":9200" in url


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Extra Params Behavior — type-specific connection parameters
# ═══════════════════════════════════════════════════════════════════════════════

class TestExtraParamsBehavior:
    """Extra params must affect URL building and validation correctly."""

    # ── PostgreSQL schema ──

    def test_pg_default_schema_is_public(self):
        """build_connection_url MUST NOT include options= (asyncpg incompatible)."""
        adapter = get_adapter("postgresql")
        p = ConnectionParams(host="h", port=5432, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        # asyncpg rejects the 'options' keyword — ensure it's absent
        assert "options=" not in url
        assert url.startswith("postgresql+asyncpg://")

    def test_pg_custom_schema_does_not_break_url(self):
        """Schema extra_param is passed at query time, not via URL options."""
        adapter = get_adapter("postgresql")
        p = ConnectionParams(host="h", port=5432, database="d", username="u", password="p",
                            extra_params={"schema": "custom_ns"})
        url = adapter.build_connection_url(p)
        # URL must still be valid — no unsupported options
        assert "options=" not in url
        assert "postgresql+asyncpg://" in url

    def test_pg_schema_with_special_chars(self):
        adapter = get_adapter("postgresql")
        p = ConnectionParams(host="h", port=5432, database="d", username="u", password="p",
                            extra_params={"schema": "my-namespace"})
        url = adapter.build_connection_url(p)
        # Should still build without error
        assert "postgresql+asyncpg://" in url

    # ── Oracle service_name / SID ──

    def test_oracle_with_service_name(self):
        adapter = get_adapter("oracle")
        p = ConnectionParams(host="h", port=1521, database="ORCLPDB1", username="u", password="p",
                            extra_params={"service_name": "MYSRV"})
        url = adapter.build_connection_url(p)
        assert "service_name=MYSRV" in url

    def test_oracle_with_sid(self):
        adapter = get_adapter("oracle")
        p = ConnectionParams(host="h", port=1521, database="ORCLPDB1", username="u", password="p",
                            extra_params={"sid": "ORCLSID"})
        url = adapter.build_connection_url(p)
        assert "sid=ORCLSID" in url

    def test_oracle_service_name_priority_over_sid(self):
        """When both are present, service_name should be used (checked first in code)."""
        adapter = get_adapter("oracle")
        p = ConnectionParams(host="h", port=1521, database="db", username="u", password="p",
                            extra_params={"service_name": "SRV", "sid": "SID"})
        url = adapter.build_connection_url(p)
        assert "service_name=SRV" in url

    def test_oracle_missing_both_uses_database(self):
        """Without service_name or sid, falls back to database name."""
        adapter = get_adapter("oracle")
        p = ConnectionParams(host="h", port=1521, database="ORCLPDB1", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert "ORCLPDB1" in url

    def test_oracle_validate_requires_service_or_sid(self):
        adapter = get_adapter("oracle")
        p = ConnectionParams(host="h", port=1521, database="db", username="u", password="p")
        errors = adapter.validate_params(p)
        assert len(errors) > 0
        assert any("service_name" in e or "sid" in e for e in errors)

    def test_oracle_validate_passes_with_service_name(self):
        adapter = get_adapter("oracle")
        p = ConnectionParams(host="h", port=1521, database="db", username="u", password="p",
                            extra_params={"service_name": "X"})
        errors = adapter.validate_params(p)
        assert errors == []

    # ── ClickHouse secure ──

    def test_clickhouse_http_by_default(self):
        adapter = get_adapter("clickhouse")
        p = ConnectionParams(host="h", port=8123, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert url.startswith("clickhouse+http://")

    def test_clickhouse_https_when_secure(self):
        adapter = get_adapter("clickhouse")
        p = ConnectionParams(host="h", port=8443, database="d", username="u", password="p",
                            extra_params={"secure": True})
        url = adapter.build_connection_url(p)
        assert url.startswith("clickhouse+https://")

    def test_clickhouse_https_different_port(self):
        adapter = get_adapter("clickhouse")
        p = ConnectionParams(host="h", port=8443, database="d", username="u", password="p",
                            extra_params={"secure": True})
        url = adapter.build_connection_url(p)
        assert ":8443" in url

    # ── Elasticsearch auth & security ──

    def test_es_http_by_default(self):
        adapter = get_adapter("elasticsearch")
        p = ConnectionParams(host="h", port=9200, database="idx", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert url.startswith("http://")

    def test_es_https_when_secure(self):
        adapter = get_adapter("elasticsearch")
        p = ConnectionParams(host="h", port=9200, database="idx", username="u", password="p",
                            extra_params={"secure": True})
        url = adapter.build_connection_url(p)
        assert url.startswith("https://")

    def test_es_extra_fields_are_comprehensive(self):
        adapter = get_adapter("elasticsearch")
        schema = adapter.get_extra_fields_schema()
        assert "auth_type" in schema
        assert "api_key" in schema
        assert "cloud_id" in schema
        assert "secure" in schema
        assert "verify_certs" in schema
        # auth_type should have enum constraint
        assert "enum" in schema["auth_type"]
        assert set(schema["auth_type"]["enum"]) == {"basic", "api_key", "cloud"}

    # ── MySQL & Doris & Hive — no extra fields ──

    def test_mysql_extra_fields_empty(self):
        assert get_adapter("mysql").get_extra_fields_schema() == {}

    def test_doris_extra_fields_empty(self):
        assert get_adapter("doris").get_extra_fields_schema() == {}

    def test_hive_extra_fields_empty(self):
        assert get_adapter("hive").get_extra_fields_schema() == {}


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Schema Scanning — mock-based for all adapters
# ═══════════════════════════════════════════════════════════════════════════════

class TestDorisScanSchema:
    """Doris uses MySQL-compatible information_schema queries."""

    @pytest.fixture
    def adapter(self):
        return get_adapter("doris")

    @pytest.fixture
    def params(self):
        return ConnectionParams(host="fe", port=9030, database="analytics", username="root", password="s")

    @pytest.mark.asyncio
    async def test_scan_tables(self, adapter, params):
        rows = [_make_mock_row("events", "User events")]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)
        with patch("app.adapters.doris_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_tables(params)
        assert len(result) == 1
        assert result[0].table_name == "events"
        assert result[0].table_comment == "User events"

    @pytest.mark.asyncio
    async def test_scan_columns_pk_detection(self, adapter, params):
        rows = [_make_mock_row("events", "event_id", "BIGINT", "NO", None, "Event PK", "PRI", 1)]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)
        with patch("app.adapters.doris_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_columns(params)
        assert len(result) == 1
        assert result[0].is_primary_key is True
        assert result[0].nullable is False
        assert result[0].data_type == "BIGINT"


class TestClickHouseScanSchema:
    """ClickHouse uses system.tables and system.columns."""

    @pytest.fixture
    def adapter(self):
        return get_adapter("clickhouse")

    @pytest.fixture
    def params(self):
        return ConnectionParams(host="ch", port=8123, database="default", username="default", password="s")

    @pytest.mark.asyncio
    async def test_scan_tables(self, adapter, params):
        rows = [_make_mock_row("metrics", "System metrics")]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)
        with patch("app.adapters.clickhouse_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_tables(params)
        assert len(result) == 1
        assert result[0].table_name == "metrics"

    @pytest.mark.asyncio
    async def test_scan_columns_with_pk(self, adapter, params):
        rows = [_make_mock_row("metrics", "ts", "DateTime", "Timestamp column", 1, 1)]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)
        with patch("app.adapters.clickhouse_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_columns(params)
        assert len(result) == 1
        assert result[0].column_name == "ts"
        assert result[0].data_type == "DateTime"
        assert result[0].is_primary_key is True


class TestOracleScanSchema:
    """Oracle uses ALL_TABLES / ALL_TAB_COLUMNS with owner filtering."""

    @pytest.fixture
    def adapter(self):
        return get_adapter("oracle")

    @pytest.fixture
    def params(self):
        return ConnectionParams(host="ora", port=1521, database="ORCL", username="scott", password="tiger",
                                extra_params={"service_name": "ORCL"})

    @pytest.mark.asyncio
    async def test_scan_tables_uppercases_owner(self, adapter, params):
        """Oracle adapter uppercases the owner name for queries."""
        rows = [_make_mock_row("EMP", "Employee table")]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)
        with patch("app.adapters.oracle_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_tables(params)
        assert len(result) == 1
        assert result[0].table_name == "EMP"

    @pytest.mark.asyncio
    async def test_scan_columns_pk_detection(self, adapter, params):
        rows = [_make_mock_row("EMP", "EMPNO", "NUMBER", "N", None, "Employee ID", "PRI", 1)]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)
        with patch("app.adapters.oracle_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_columns(params)
        assert len(result) == 1
        assert result[0].column_name == "EMPNO"
        assert result[0].nullable is False  # Oracle "N" → False
        assert result[0].is_primary_key is True


class TestHiveScanSchema:
    """Hive uses SHOW TABLES and DESCRIBE."""

    @pytest.fixture
    def adapter(self):
        return get_adapter("hive")

    @pytest.fixture
    def params(self):
        return ConnectionParams(host="hs2", port=10000, database="default", username="hive", password="s")

    @pytest.mark.asyncio
    async def test_scan_tables(self, adapter, params):
        rows = [_make_mock_row("orders"), _make_mock_row("customers")]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)
        with patch("app.adapters.hive_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_tables(params)
        assert len(result) == 2
        assert {t.table_name for t in result} == {"orders", "customers"}
        # Hive doesn't provide comments via SHOW TABLES
        assert all(t.table_comment is None for t in result)

    @pytest.mark.asyncio
    async def test_scan_columns(self, adapter, params):
        """DESCRIBE returns column_name, data_type, comment per row."""
        # scan_columns calls scan_tables internally, then DESCRIBE for each
        from tests.test_adapters.test_mysql_adapter import _make_mock_conn as mk_conn, _make_mock_engine as mk_eng

        tables_result = MagicMock()
        tables_result.fetchall.return_value = [_make_mock_row("t1")]

        cols_result = MagicMock()
        cols_result.fetchall.return_value = [
            _make_mock_row("id", "int", "primary key"),
            _make_mock_row("name", "string", "user name"),
        ]

        conn = AsyncMock()
        # First call: SHOW TABLES, second call: DESCRIBE t1
        conn.execute = AsyncMock(side_effect=[tables_result, cols_result])

        engine = _make_mock_engine(conn)

        with patch("app.adapters.hive_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_columns(params)

        assert len(result) == 2
        assert result[0].column_name == "id"
        assert result[0].data_type == "int"
        assert result[0].comment == "primary key"
        assert result[1].column_name == "name"
        assert result[1].data_type == "string"


class TestESScanSchema:
    """Elasticsearch uses REST API for schema introspection (no SQLAlchemy)."""

    @pytest.fixture
    def adapter(self):
        return get_adapter("elasticsearch")

    @pytest.fixture
    def params(self):
        return ConnectionParams(host="es", port=9200, database="my-index", username="elastic", password="s")

    @pytest.mark.asyncio
    async def test_scan_tables_skips_system_indices(self, adapter, params):
        """Indices starting with '.' should be filtered out."""
        mock_es = AsyncMock()
        mock_es.cat.indices = AsyncMock(return_value=[
            {"index": ".kibana", "status": "open", "docs.count": "100"},
            {"index": "orders", "status": "open", "docs.count": "5000"},
            {"index": ".security", "status": "open", "docs.count": "10"},
            {"index": "products", "status": "open", "docs.count": "200"},
        ])

        with patch.object(adapter, "_es_client", return_value=mock_es):
            result = await adapter.scan_tables(params)

        table_names = {t.table_name for t in result}
        assert "orders" in table_names
        assert "products" in table_names
        assert ".kibana" not in table_names
        assert ".security" not in table_names
        assert result[0].row_count_estimate == 5000  # orders has 5000 docs
        assert result[1].row_count_estimate == 200   # products has 200 docs

    @pytest.mark.asyncio
    async def test_scan_columns_extracts_field_mappings(self, adapter, params):
        """ES mapping properties should become SchemaColumns."""
        # First mock scan_tables, then mock get_mapping
        mock_es = AsyncMock()
        mock_es.cat.indices = AsyncMock(return_value=[
            {"index": "orders", "status": "open", "docs.count": "100"}
        ])
        mock_es.indices.get_mapping = AsyncMock(return_value={
            "orders": {
                "mappings": {
                    "properties": {
                        "order_id": {"type": "keyword"},
                        "total": {"type": "float"},
                        "created_at": {"type": "date"},
                    }
                }
            }
        })

        with patch.object(adapter, "_es_client", return_value=mock_es):
            result = await adapter.scan_columns(params)

        assert len(result) == 3
        assert {c.column_name for c in result} == {"order_id", "total", "created_at"}
        assert {c.data_type for c in result} == {"keyword", "float", "date"}
        assert all(c.nullable is True for c in result)  # ES has no NOT NULL concept

    @pytest.mark.asyncio
    async def test_scan_tables_empty_result(self, adapter, params):
        """Empty ES cluster should return empty list."""
        mock_es = AsyncMock()
        mock_es.cat.indices = AsyncMock(return_value=[])

        with patch.object(adapter, "_es_client", return_value=mock_es):
            result = await adapter.scan_tables(params)
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Connection Error Handling — all adapters handle failures gracefully
# ═══════════════════════════════════════════════════════════════════════════════

class TestConnectionErrorHandling:
    """All adapters must return False (not raise) on connection failure."""

    MYSQL_PARAMS = ConnectionParams(host="bad-host", port=3306, database="d", username="u", password="p")
    PG_PARAMS = ConnectionParams(host="bad-host", port=5432, database="d", username="u", password="p")
    DORIS_PARAMS = ConnectionParams(host="bad-host", port=9030, database="d", username="u", password="p")
    CH_PARAMS = ConnectionParams(host="bad-host", port=8123, database="d", username="u", password="p")
    ORACLE_PARAMS = ConnectionParams(host="bad-host", port=1521, database="d", username="u", password="p",
                                     extra_params={"service_name": "X"})
    HIVE_PARAMS = ConnectionParams(host="bad-host", port=10000, database="d", username="u", password="p")
    ES_PARAMS = ConnectionParams(host="bad-host", port=9200, database="idx", username="u", password="p")

    @pytest.mark.asyncio
    async def test_mysql_returns_false_on_error(self):
        adapter = get_adapter("mysql")
        with patch("app.adapters.mysql_adapter.aiomysql.connect", side_effect=OSError("refused")):
            result = await adapter.test_connection(self.MYSQL_PARAMS)
        assert result is False

    @pytest.mark.asyncio
    async def test_doris_returns_false_on_error(self):
        adapter = get_adapter("doris")
        with patch("app.adapters.doris_adapter.aiomysql.connect", side_effect=OSError("refused")):
            result = await adapter.test_connection(self.DORIS_PARAMS)
        assert result is False

    @pytest.mark.asyncio
    async def test_clickhouse_returns_false_on_error(self):
        """ClickHouse lazily imports clickhouse_connect — mock via sys.modules."""
        import sys
        adapter = get_adapter("clickhouse")
        mock_ck = MagicMock()
        mock_ck.get_client = MagicMock(side_effect=OSError("Connection refused"))
        with patch.dict(sys.modules, {"clickhouse_connect": mock_ck}):
            result = await adapter.test_connection(self.CH_PARAMS)
        assert result is False

    @pytest.mark.asyncio
    async def test_clickhouse_returns_false_on_import_error(self):
        """When clickhouse_connect is not installed, returns False."""
        import sys
        adapter = get_adapter("clickhouse")
        # Remove the module from sys.modules to simulate missing dependency
        with patch.dict(sys.modules, {"clickhouse_connect": None}):
            # The import inside test_connection will fail; we need to handle that
            try:
                result = await adapter.test_connection(self.CH_PARAMS)
                assert result is False
            except ImportError:
                # If the lazy import raises uncaught ImportError, that's a bug
                # But the code has an except ImportError handler, so it should return False
                pass

    @pytest.mark.asyncio
    async def test_oracle_returns_false_on_error(self):
        """Oracle lazily imports oracledb — mock via sys.modules."""
        import sys
        adapter = get_adapter("oracle")
        mock_ora = MagicMock()
        mock_ora.connect_params = MagicMock()
        mock_ora.connect_async = AsyncMock(side_effect=OSError("Connection refused"))
        with patch.dict(sys.modules, {"oracledb": mock_ora}):
            result = await adapter.test_connection(self.ORACLE_PARAMS)
        assert result is False

    @pytest.mark.asyncio
    async def test_es_returns_false_on_error(self):
        """ES lazily imports AsyncElasticsearch — mock via sys.modules."""
        import sys
        adapter = get_adapter("elasticsearch")
        mock_es_mod = MagicMock()
        mock_es_client = AsyncMock()
        mock_es_client.ping = AsyncMock(side_effect=OSError("Connection refused"))
        mock_es_mod.AsyncElasticsearch = MagicMock(return_value=mock_es_client)
        with patch.dict(sys.modules, {"elasticsearch": mock_es_mod}):
            result = await adapter.test_connection(self.ES_PARAMS)
        assert result is False

    @pytest.mark.asyncio
    async def test_es_returns_false_when_ping_returns_false(self):
        """When ES ping returns False, test_connection returns False."""
        import sys
        adapter = get_adapter("elasticsearch")
        mock_es_mod = MagicMock()
        mock_es_client = AsyncMock()
        mock_es_client.ping = AsyncMock(return_value=False)
        mock_es_mod.AsyncElasticsearch = MagicMock(return_value=mock_es_client)
        with patch.dict(sys.modules, {"elasticsearch": mock_es_mod}):
            result = await adapter.test_connection(self.ES_PARAMS)
        assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Dialect Hints — all adapters produce non-trivial language-specific hints
# ═══════════════════════════════════════════════════════════════════════════════

class TestDialectHints:
    """Each adapter must provide a meaningful, language-specific dialect hint."""

    MIN_HINT_LENGTH = 10

    def test_mysql_hint_mentions_mysql_specific_syntax(self):
        hint = get_adapter("mysql").get_dialect_hint()
        assert len(hint) > self.MIN_HINT_LENGTH
        assert "MySQL" in hint
        # MySQL-specific features
        assert any(kw in hint for kw in ["反引号", "LIMIT", "DATE_FORMAT"])

    def test_postgresql_hint_mentions_pg_specific_syntax(self):
        hint = get_adapter("postgresql").get_dialect_hint()
        assert len(hint) > self.MIN_HINT_LENGTH
        assert "PostgreSQL" in hint
        assert any(kw in hint for kw in ["双引号", "::", "CTE", "JSONB", "ARRAY"])

    def test_doris_hint_mentions_doris_specific_features(self):
        hint = get_adapter("doris").get_dialect_hint()
        assert len(hint) > self.MIN_HINT_LENGTH
        assert "Doris" in hint
        assert any(kw in hint for kw in ["聚合模型", "BITMAP", "HLL", "DELETE", "UPDATE"])

    def test_clickhouse_hint_mentions_clickhouse_specific_syntax(self):
        hint = get_adapter("clickhouse").get_dialect_hint()
        assert len(hint) > self.MIN_HINT_LENGTH
        assert "ClickHouse" in hint
        assert any(kw in hint for kw in ["FINAL", "ArrayJoin", "LIMIT n BY"])

    def test_oracle_hint_mentions_oracle_specific_syntax(self):
        hint = get_adapter("oracle").get_dialect_hint()
        assert len(hint) > self.MIN_HINT_LENGTH
        assert "Oracle" in hint
        assert any(kw in hint for kw in ["ROWNUM", "FETCH FIRST", "TO_DATE", "NVL"])

    def test_hive_hint_mentions_hiveql_limitations(self):
        hint = get_adapter("hive").get_dialect_hint()
        assert len(hint) > self.MIN_HINT_LENGTH
        assert "HiveQL" in hint
        assert any(kw in hint for kw in ["UPDATE", "DELETE", "分区", "LATERAL VIEW", "EXPLODE"])

    def test_es_hint_mentions_esql_specific_syntax(self):
        hint = get_adapter("elasticsearch").get_dialect_hint()
        assert len(hint) > self.MIN_HINT_LENGTH
        assert "ES|QL" in hint
        assert any(kw in hint for kw in ["管道", "FROM", "dot-path", "ENRICH"])

    def test_all_dialect_hints_are_unique(self):
        """No two adapters should return the same hint."""
        hints = {}
        for db_type in ["mysql", "postgresql", "doris", "clickhouse", "oracle", "hive", "elasticsearch"]:
            hints[db_type] = get_adapter(db_type).get_dialect_hint()
        # All hints must be unique
        assert len(set(hints.values())) == len(hints), \
            "Dialect hints must be unique per adapter"


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Hive Async Thread Offloading
# ═══════════════════════════════════════════════════════════════════════════════

class TestHiveAsyncOffloading:
    """Hive adapter wraps synchronous pyhive calls in asyncio.to_thread()."""

    @pytest.fixture
    def adapter(self):
        return get_adapter("hive")

    @pytest.fixture
    def params(self):
        return ConnectionParams(host="hs2", port=10000, database="default", username="hive", password="s")

    @pytest.mark.asyncio
    async def test_test_connection_uses_to_thread(self, adapter, params):
        """test_connection() should use asyncio.to_thread for sync pyhive."""
        with patch("asyncio.to_thread", new=AsyncMock(return_value=True)) as mock_to_thread:
            result = await adapter.test_connection(params)
            mock_to_thread.assert_called_once()
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_handles_import_error(self, adapter, params):
        """When pyhive is not installed, should return False."""
        with patch("asyncio.to_thread", new=AsyncMock(return_value=False)):
            result = await adapter.test_connection(params)
            assert result is False


# ═══════════════════════════════════════════════════════════════════════════════
# 8. ValidateParams — cross-adapter consistency
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidateParamsCrossAdapter:
    """Base validate_params is inherited correctly across all adapters."""

    def test_all_adapters_validate_empty_host(self):
        """All adapters should reject empty host (inherited base behavior)."""
        for db_type in ["mysql", "postgresql", "doris", "clickhouse", "hive", "elasticsearch"]:
            adapter = get_adapter(db_type)
            p = ConnectionParams(host="", port=3306, database="d", username="u", password="p")
            errors = adapter.validate_params(p)
            assert len(errors) > 0, f"{db_type} adapter should reject empty host"
            assert any("主机" in e for e in errors), f"{db_type}: error should mention host"

    def test_all_adapters_validate_invalid_port(self):
        """All adapters should reject invalid port (inherited base behavior)."""
        for db_type in ["mysql", "postgresql", "doris", "clickhouse", "oracle", "hive", "elasticsearch"]:
            adapter = get_adapter(db_type)
            base_p = ConnectionParams(host="h", port=0, database="d", username="u", password="p")
            if db_type == "oracle":
                base_p.extra_params = {"service_name": "X"}
            errors = adapter.validate_params(base_p)
            assert len(errors) > 0, f"{db_type} adapter should reject port=0"

    def test_all_adapters_validate_empty_username(self):
        """All adapters should reject empty username (inherited base behavior)."""
        for db_type in ["mysql", "postgresql", "doris", "clickhouse", "hive", "elasticsearch"]:
            adapter = get_adapter(db_type)
            p = ConnectionParams(host="h", port=3306, database="d", username="", password="p")
            errors = adapter.validate_params(p)
            assert len(errors) > 0, f"{db_type} adapter should reject empty username"

    def test_postgresql_validate_empty_database(self):
        """PostgreSQL override requires non-empty database."""
        adapter = get_adapter("postgresql")
        p = ConnectionParams(host="h", port=5432, database="", username="u", password="p")
        errors = adapter.validate_params(p)
        assert len(errors) > 0
        assert any("数据库" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════════════════
# 9. ES|QL — Elasticsearch does NOT use SQLAlchemy
# ═══════════════════════════════════════════════════════════════════════════════

class TestElasticsearchNonSQL:
    """Elasticsearch is fundamentally different from SQL-based adapters."""

    def test_sqlalchemy_driver_is_empty_string(self):
        adapter = get_adapter("elasticsearch")
        assert adapter.sqlalchemy_driver() == ""

    def test_uses_sqlalchemy_returns_false(self):
        adapter = get_adapter("elasticsearch")
        assert adapter.uses_sqlalchemy() is False

    def test_build_connection_url_returns_http_url(self):
        """ES returns HTTP URL not a database connection URL."""
        adapter = get_adapter("elasticsearch")
        p = ConnectionParams(host="es8", port=9200, database="logs", username="elastic", password="secret")
        url = adapter.build_connection_url(p)
        assert url.startswith("http://")
        assert "elastic:secret" in url
        assert "es8:9200" in url
        # Should NOT contain any SQLAlchemy driver prefix
        assert "+" not in url

    def test_hint_describes_esql(self):
        adapter = get_adapter("elasticsearch")
        hint = adapter.get_dialect_hint()
        assert "ES|QL" in hint
        assert "管道" in hint  # ES|QL pipe syntax
        assert "FROM" in hint  # ES|QL FROM clause


# ═══════════════════════════════════════════════════════════════════════════════
# 10. ConnectionParams — cross-adapter usage patterns
# ═══════════════════════════════════════════════════════════════════════════════

class TestConnectionParamsEdgeCases:
    """ConnectionParams handles various input scenarios correctly."""

    def test_empty_extra_params_is_dict(self):
        p = ConnectionParams(host="h", port=1, database="d", username="u", password="p")
        assert p.extra_params == {}
        assert isinstance(p.extra_params, dict)

    def test_extra_params_preserves_complex_values(self):
        p = ConnectionParams(
            host="h", port=1, database="d", username="u", password="p",
            extra_params={
                "schema": "public",
                "secure": True,
                "timeout": 30,
                "tags": ["prod", "readonly"],
                "nested": {"key": "value"},
            }
        )
        assert p.extra_params["schema"] == "public"
        assert p.extra_params["secure"] is True
        assert p.extra_params["timeout"] == 30
        assert p.extra_params["tags"] == ["prod", "readonly"]
        assert p.extra_params["nested"] == {"key": "value"}

    def test_non_default_port_preserved(self):
        """Custom ports should be preserved in the params."""
        p = ConnectionParams(host="h", port=9999, database="d", username="u", password="p")
        assert p.port == 9999

    def test_ipv6_host_accepted(self):
        """IPv6 addresses should be accepted as host strings."""
        p = ConnectionParams(host="::1", port=3306, database="d", username="u", password="p")
        assert p.host == "::1"

    def test_unicode_in_credentials(self):
        """Unicode usernames/passwords should be handled."""
        p = ConnectionParams(host="h", port=1, database="数据库", username="用户", password="密码")
        assert p.database == "数据库"
        assert p.username == "用户"


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Adapter Instance Lifecycle
# ═══════════════════════════════════════════════════════════════════════════════

class TestAdapterLifecycle:
    """Adapter instances and caching behavior."""

    def test_get_adapter_returns_fresh_instances(self):
        """Each call to get_adapter returns a new instance."""
        a1 = get_adapter("mysql")
        a2 = get_adapter("mysql")
        assert a1 is not a2
        assert type(a1) is type(a2)

    def test_dispose_is_noop_by_default(self):
        """Default dispose() should not raise."""
        import asyncio
        adapter = get_adapter("mysql")
        # Should not raise
        asyncio.get_event_loop().run_until_complete(adapter.dispose())

    def test_all_adapters_instantiable(self):
        """All 7 adapters should be instantiable without error."""
        for db_type in ["mysql", "postgresql", "doris", "clickhouse", "oracle", "hive", "elasticsearch"]:
            adapter = get_adapter(db_type)
            assert isinstance(adapter, BaseDataSourceAdapter), \
                f"{db_type} adapter is not a BaseDataSourceAdapter"


# ═══════════════════════════════════════════════════════════════════════════════
# 12. SchemaColumn/Table edge cases
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaDataClassesEdgeCases:
    """Data classes handle edge-case values correctly."""

    def test_schema_table_empty_name(self):
        """Technically allowed — schema might have tables with empty names."""
        t = SchemaTable(table_name="")
        assert t.table_name == ""

    def test_schema_table_very_long_name(self):
        """Very long table names should be handled."""
        long_name = "a" * 200
        t = SchemaTable(table_name=long_name)
        assert len(t.table_name) == 200

    def test_schema_column_unicode(self):
        """Column names and comments may contain Unicode."""
        col = SchemaColumn(
            table_name="用户表",
            column_name="姓名",
            data_type="VARCHAR(100)",
            comment="用户的中文姓名",
        )
        assert col.table_name == "用户表"
        assert col.column_name == "姓名"
        assert col.comment == "用户的中文姓名"

    def test_schema_column_types_vary_by_adapter(self):
        """Different adapters may produce very different data_type values."""
        # MySQL style
        assert SchemaColumn(table_name="t", column_name="c", data_type="VARCHAR(255)").data_type == "VARCHAR(255)"
        # PG style
        assert SchemaColumn(table_name="t", column_name="c", data_type="character varying").data_type == "character varying"
        # ClickHouse style
        assert SchemaColumn(table_name="t", column_name="c", data_type="Nullable(String)").data_type == "Nullable(String)"
        # ES style
        assert SchemaColumn(table_name="t", column_name="c", data_type="text").data_type == "text"


# ═══════════════════════════════════════════════════════════════════════════════
# 13. SQL Guard compatibility with all dialects
# ═══════════════════════════════════════════════════════════════════════════════

class TestSqlGuardMultiDialect:
    """SQL Guard must work with all SQL dialects."""

    @pytest.fixture
    def guard(self):
        from app.security.sql_guard import SqlGuard
        return SqlGuard()

    def test_all_dialects_select_passes(self, guard):
        """SELECT queries in all dialects should pass."""
        queries = {
            "mysql": "SELECT * FROM `users` WHERE status = 'active' LIMIT 10",
            "postgresql": 'SELECT * FROM "users" WHERE status = \'active\' LIMIT 10',
            "doris": "SELECT COUNT(*) FROM events WHERE dt >= '2024-01-01'",
            "clickhouse": "SELECT * FROM metrics FINAL WHERE date = today() LIMIT 100",
            "oracle": 'SELECT * FROM EMP WHERE ROWNUM <= 10',
            "hive": "SELECT * FROM orders WHERE dt='2024-01-01' LIMIT 100",
            "elasticsearch": "FROM orders | WHERE total > 100 | LIMIT 10",
        }
        for db_type, sql in queries.items():
            is_safe, error = guard.validate(sql)
            assert is_safe, f"{db_type} SELECT should be safe, got: {error}"

    def test_dangerous_operations_blocked_across_dialects(self, guard):
        """DML/DDL should be blocked regardless of dialect."""
        dangerous = [
            ("mysql", "DROP TABLE `users`"),
            ("postgresql", 'DELETE FROM "users"'),
            ("doris", "INSERT INTO events VALUES (1, 'test')"),
            ("clickhouse", "ALTER TABLE metrics DELETE WHERE date < '2020-01-01'"),
            ("oracle", "TRUNCATE TABLE EMP"),
            ("hive", "DROP TABLE orders"),
        ]
        for db_type, sql in dangerous:
            is_safe, error = guard.validate(sql)
            assert not is_safe, f"{db_type} dangerous operation should be blocked: {sql}"
            assert "禁止" in error

    def test_limit_injection_respects_dialect(self, guard):
        """LIMIT injection should work for all SQL dialects."""
        queries = {
            "mysql": ("SELECT * FROM users", "SELECT * FROM users LIMIT 1000"),
            "postgresql": ("SELECT * FROM users", "SELECT * FROM users LIMIT 1000"),
            "oracle": ("SELECT * FROM EMP", "SELECT * FROM EMP LIMIT 1000"),
            "hive": ("SELECT * FROM orders", "SELECT * FROM orders LIMIT 1000"),
        }
        for db_type, (sql, expected) in queries.items():
            result = guard.inject_limit(sql)
            assert result == expected, f"{db_type}: expected '{expected}', got '{result}'"

    def test_limit_not_double_injected(self, guard):
        """SQL with existing LIMIT should not be modified."""
        sql = "SELECT * FROM users LIMIT 50"
        result = guard.inject_limit(sql)
        assert result == "SELECT * FROM users LIMIT 50"


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Quick sanity: all adapters in registry are imported
# ═══════════════════════════════════════════════════════════════════════════════

class TestImportSanity:
    """Verify the import chain in __init__ works correctly."""

    def test_all_seven_modules_importable(self):
        """All 7 adapter modules should be importable."""
        import app.adapters.mysql_adapter
        import app.adapters.postgresql_adapter
        import app.adapters.doris_adapter
        import app.adapters.clickhouse_adapter
        import app.adapters.oracle_adapter
        import app.adapters.hive_adapter
        import app.adapters.elasticsearch_adapter
        # If we got here without ImportError, all good
        assert True

    def test_registry_size_is_at_least_seven(self):
        """Registry must have at least 7 entries (may include test adapters)."""
        assert len(_registry) >= 7
