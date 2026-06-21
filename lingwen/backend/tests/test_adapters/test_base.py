"""Contract tests for BaseDataSourceAdapter ABC.

These tests validate the abstract base class contract:
- All abstract methods are declared
- Data classes work correctly
- A minimal concrete subclass can be instantiated and satisfies the interface
"""

import pytest
from app.adapters.base import (
    BaseDataSourceAdapter,
    ConnectionParams,
    SchemaColumn,
    SchemaTable,
)


# ── Minimal concrete adapter for testing the ABC ──
class _DummyAdapter(BaseDataSourceAdapter):
    """A fully concrete adapter used only in tests."""

    @staticmethod
    def db_type() -> str:
        return "dummy"

    @staticmethod
    def display_name() -> str:
        return "Dummy DB"

    @staticmethod
    def default_port() -> int:
        return 9999

    @staticmethod
    def sqlalchemy_driver() -> str:
        return "dummy+driver"

    def build_connection_url(self, params: ConnectionParams) -> str:
        return f"dummy+driver://{params.username}@{params.host}:{params.port}/{params.database}"

    async def test_connection(self, params: ConnectionParams) -> bool:
        return True

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        return [SchemaTable(table_name="test_table")]

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        return [
            SchemaColumn(
                table_name="test_table",
                column_name="id",
                data_type="INTEGER",
                nullable=False,
                default_value=None,
                comment="primary key",
                is_primary_key=True,
                ordinal_position=1,
            )
        ]

    def get_dialect_hint(self) -> str:
        return "Dummy SQL dialect"

    def get_extra_fields_schema(self) -> dict:
        return {"extra_field": {"type": "string", "default": "value"}}


# ── Fixtures ──
@pytest.fixture
def adapter() -> _DummyAdapter:
    """Return a fresh concrete adapter for each test."""
    return _DummyAdapter()


@pytest.fixture
def params() -> ConnectionParams:
    """Return a valid set of connection parameters."""
    return ConnectionParams(
        host="localhost",
        port=3306,
        database="testdb",
        username="testuser",
        password="secret",
    )


# ── Tests: ConnectionParams ──
class TestConnectionParams:
    """Tests for the ConnectionParams data class."""

    def test_default_extra_params_empty(self):
        """extra_params defaults to an empty dict."""
        p = ConnectionParams(host="h", port=1, database="d", username="u", password="p")
        assert p.extra_params == {}

    def test_extra_params_stores_values(self):
        """extra_params accepts arbitrary key-value pairs."""
        p = ConnectionParams(
            host="h", port=1, database="d", username="u", password="p",
            extra_params={"schema": "public", "ssl": True},
        )
        assert p.extra_params["schema"] == "public"
        assert p.extra_params["ssl"] is True

    def test_all_fields_accessible(self, params):
        """All fields are accessible as attributes."""
        assert params.host == "localhost"
        assert params.port == 3306
        assert params.database == "testdb"
        assert params.username == "testuser"
        assert params.password == "secret"


# ── Tests: SchemaTable ──
class TestSchemaTable:
    """Tests for the SchemaTable data class."""

    def test_minimal_creation(self):
        """SchemaTable can be created with only table_name."""
        tbl = SchemaTable(table_name="users")
        assert tbl.table_name == "users"
        assert tbl.table_comment is None
        assert tbl.row_count_estimate is None

    def test_full_creation(self):
        """SchemaTable accepts all optional fields."""
        tbl = SchemaTable(
            table_name="orders",
            table_comment="Customer orders",
            row_count_estimate=5000,
        )
        assert tbl.table_name == "orders"
        assert tbl.table_comment == "Customer orders"
        assert tbl.row_count_estimate == 5000


# ── Tests: SchemaColumn ──
class TestSchemaColumn:
    """Tests for the SchemaColumn data class."""

    def test_minimal_creation(self):
        """SchemaColumn can be created with only required fields."""
        col = SchemaColumn(
            table_name="users",
            column_name="id",
            data_type="INTEGER",
            nullable=False,
            default_value=None,
            comment=None,
        )
        assert col.table_name == "users"
        assert col.column_name == "id"
        assert col.data_type == "INTEGER"
        assert col.is_primary_key is False
        assert col.ordinal_position == 0

    def test_full_creation(self):
        """SchemaColumn accepts all fields including is_primary_key and ordinal_position."""
        col = SchemaColumn(
            table_name="users",
            column_name="email",
            data_type="VARCHAR(255)",
            nullable=False,
            default_value="N/A",
            comment="User email address",
            is_primary_key=False,
            ordinal_position=2,
        )
        assert col.table_name == "users"
        assert col.column_name == "email"
        assert col.data_type == "VARCHAR(255)"
        assert col.nullable is False
        assert col.default_value == "N/A"
        assert col.comment == "User email address"
        assert col.is_primary_key is False
        assert col.ordinal_position == 2


# ── Tests: Abstract class contract ──
class TestBaseAdapterContract:
    """Tests verifying that the ABC contract is properly enforced."""

    def test_cannot_instantiate_abc_directly(self):
        """Instantiating the ABC directly should raise TypeError."""
        with pytest.raises(TypeError):
            BaseDataSourceAdapter()  # type: ignore[abstract]

    def test_concrete_subclass_instantiates(self, adapter):
        """A fully concrete subclass can be instantiated."""
        assert isinstance(adapter, BaseDataSourceAdapter)

    def test_db_type_is_string(self, adapter):
        """db_type() returns a non-empty string."""
        result = adapter.db_type()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_display_name_is_string(self, adapter):
        """display_name() returns a non-empty string."""
        result = adapter.display_name()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_default_port_is_int(self, adapter):
        """default_port() returns a positive integer."""
        result = adapter.default_port()
        assert isinstance(result, int)
        assert result > 0

    def test_sqlalchemy_driver_is_string(self, adapter):
        """sqlalchemy_driver() returns a non-empty string."""
        result = adapter.sqlalchemy_driver()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_build_connection_url_returns_string(self, adapter, params):
        """build_connection_url() returns a URL string."""
        url = adapter.build_connection_url(params)
        assert isinstance(url, str)
        assert len(url) > 0

    def test_build_connection_url_contains_host(self, adapter, params):
        """build_connection_url() includes the host."""
        url = adapter.build_connection_url(params)
        assert params.host in url

    @pytest.mark.asyncio
    async def test_test_connection_returns_bool(self, adapter, params):
        """test_connection() returns a boolean."""
        result = await adapter.test_connection(params)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_scan_tables_returns_list(self, adapter, params):
        """scan_tables() returns a list of SchemaTable."""
        result = await adapter.scan_tables(params)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, SchemaTable)

    @pytest.mark.asyncio
    async def test_scan_columns_returns_list(self, adapter, params):
        """scan_columns() returns a list of SchemaColumn."""
        result = await adapter.scan_columns(params)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, SchemaColumn)

    def test_get_dialect_hint_returns_non_empty_string(self, adapter):
        """get_dialect_hint() returns a non-empty string."""
        hint = adapter.get_dialect_hint()
        assert isinstance(hint, str)
        assert len(hint) > 0

    def test_get_extra_fields_schema_returns_dict(self, adapter):
        """get_extra_fields_schema() returns a dict."""
        schema = adapter.get_extra_fields_schema()
        assert isinstance(schema, dict)


# ── Tests: validate_params ──
class TestValidateParams:
    """Tests for the base validate_params() implementation."""

    def test_valid_params_returns_empty_errors(self, adapter, params):
        """Valid params should produce no error messages."""
        errors = adapter.validate_params(params)
        assert errors == []

    def test_empty_host_returns_error(self, adapter):
        """Empty host should produce an error."""
        bad = ConnectionParams(host="", port=3306, database="db", username="u", password="p")
        errors = adapter.validate_params(bad)
        assert len(errors) > 0
        assert any("主机" in e for e in errors)

    def test_invalid_port_returns_error(self, adapter):
        """Zero or negative port should produce an error."""
        bad = ConnectionParams(host="h", port=0, database="db", username="u", password="p")
        errors = adapter.validate_params(bad)
        assert len(errors) > 0

    def test_empty_username_returns_error(self, adapter):
        """Empty username should produce an error."""
        bad = ConnectionParams(host="h", port=3306, database="db", username="", password="p")
        errors = adapter.validate_params(bad)
        assert len(errors) > 0
        assert any("用户" in e for e in errors)
