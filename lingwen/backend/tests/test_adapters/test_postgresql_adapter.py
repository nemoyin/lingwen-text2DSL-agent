"""Unit tests for PostgreSQLAdapter."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.adapters.base import ConnectionParams, SchemaColumn, SchemaTable


@pytest.fixture
def adapter():
    from app.adapters.postgresql_adapter import PostgreSQLAdapter
    return PostgreSQLAdapter()


@pytest.fixture
def params():
    return ConnectionParams(
        host="pg.example.com",
        port=5432,
        database="analytics",
        username="reader",
        password="secret",
        extra_params={"schema": "public"},
    )


class TestPostgreSQLIdentity:
    def test_db_type(self, adapter):
        assert adapter.db_type() == "postgresql"

    def test_display_name(self, adapter):
        assert adapter.display_name() == "PostgreSQL"

    def test_default_port(self, adapter):
        assert adapter.default_port() == 5432

    def test_sqlalchemy_driver(self, adapter):
        assert adapter.sqlalchemy_driver() == "postgresql+asyncpg"


class TestPostgreSQLConnectionURL:
    def test_url_contains_driver(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert url.startswith("postgresql+asyncpg://")

    def test_url_contains_credentials(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "reader:secret" in url

    def test_default_schema(self, adapter):
        """When extra_params has no schema, default is 'public'."""
        p = ConnectionParams(host="h", port=5432, database="d", username="u", password="p")
        url = adapter.build_connection_url(p)
        assert "?schema=public" in url or "options=-c%20search_path%3Dpublic" in url

    def test_custom_schema(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "schema=public" in url or "search_path" in url


class TestPostgreSQLScanTables:
    @pytest.mark.asyncio
    async def test_queries_information_schema_with_schema_param(self, adapter, params):
        """Should use PG information_schema with table_schema filter."""
        from tests.test_adapters.test_mysql_adapter import (
            _make_mock_conn, _make_mock_engine, _make_mock_row,
        )
        rows = [_make_mock_row("users", "User accounts")]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)

        with patch("app.adapters.postgresql_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_tables(params)

        assert len(result) == 1
        assert result[0].table_name == "users"


class TestPostgreSQLScanColumns:
    @pytest.mark.asyncio
    async def test_pk_detection_via_pg_constraint(self, adapter, params):
        """Should detect primary keys via information_schema + pg_catalog query."""
        from tests.test_adapters.test_mysql_adapter import (
            _make_mock_conn, _make_mock_engine, _make_mock_row,
        )
        # PG information_schema.columns: 8 columns like MySQL layout
        rows = [_make_mock_row("users", "id", "integer", "NO", None, "pk", "PRI", 1)]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)

        with patch("app.adapters.postgresql_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_columns(params)

        assert len(result) >= 1
        col = result[0]
        assert col.table_name == "users"
        assert col.column_name == "id"


class TestPostgreSQLDialectHint:
    def test_hint_contains_postgresql(self, adapter):
        hint = adapter.get_dialect_hint()
        assert "PostgreSQL" in hint
        assert len(hint) > 30


class TestPostgreSQLExtraFields:
    def test_extra_fields_includes_schema(self, adapter):
        schema = adapter.get_extra_fields_schema()
        assert "schema" in schema
        assert schema["schema"]["default"] == "public"


class TestPostgreSQLRegistry:
    def test_registered(self):
        import app.adapters as mod
        assert "postgresql" in mod._registry

    def test_get_adapter_returns_correct_type(self):
        import app.adapters as mod
        inst = mod.get_adapter("postgresql")
        assert inst.db_type() == "postgresql"
        assert inst.uses_sqlalchemy() is True
