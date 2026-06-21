"""Unit tests for MySQLAdapter — extracted from existing datasource_service logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.adapters.base import ConnectionParams, SchemaColumn, SchemaTable


# ── Helpers ─────────────────────────────────────────────────────────────────


def _make_mock_engine(mock_conn):
    """Return a plain-class mock SQLAlchemy engine.

    Uses a plain class (NOT AsyncMock) because AsyncMock's magic method
    resolution forces child attribute calls to return coroutines regardless
    of ``return_value``, which breaks ``engine.connect()`` (it must return
    an async context manager, not a coroutine).
    """

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


def _make_mock_row(*values):
    """Return a MagicMock that behaves like a SQLAlchemy Row for __getitem__."""
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


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def adapter():
    """Import and return a fresh MySQLAdapter instance."""
    from app.adapters.mysql_adapter import MySQLAdapter
    return MySQLAdapter()


@pytest.fixture
def params():
    """Standard MySQL connection parameters."""
    return ConnectionParams(
        host="localhost",
        port=3306,
        database="testdb",
        username="root",
        password="secret",
    )


# ── Tests ────────────────────────────────────────────────────────────────────


class TestMySQLAdapterIdentity:
    """Static identity methods."""

    def test_db_type(self, adapter):
        assert adapter.db_type() == "mysql"

    def test_display_name(self, adapter):
        assert adapter.display_name() == "MySQL"

    def test_default_port(self, adapter):
        assert adapter.default_port() == 3306

    def test_sqlalchemy_driver(self, adapter):
        assert adapter.sqlalchemy_driver() == "mysql+aiomysql"


class TestMySQLConnectionURL:
    """build_connection_url() tests."""

    def test_url_contains_driver_prefix(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert url.startswith("mysql+aiomysql://")

    def test_url_contains_credentials(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "root:secret" in url

    def test_url_contains_host_and_port(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "localhost:3306" in url

    def test_url_contains_database(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "/testdb" in url

    def test_url_includes_charset(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "charset=utf8mb4" in url

    def test_url_special_characters_escaped(self, adapter):
        """Passwords with special chars should be URL-encoded."""
        p = ConnectionParams(
            host="h", port=1, database="d", username="u",
            password="p@ss:word!/",
        )
        url = adapter.build_connection_url(p)
        assert "p%40ss%3Aword%21%2F" in url


class TestMySQLValidateParams:
    """Parameter validation."""

    def test_valid_params_no_errors(self, adapter, params):
        errors = adapter.validate_params(params)
        assert errors == []

    def test_empty_host(self, adapter):
        p = ConnectionParams(host="", port=3306, database="d", username="u", password="p")
        errors = adapter.validate_params(p)
        assert len(errors) > 0

    def test_invalid_port(self, adapter):
        p = ConnectionParams(host="h", port=0, database="d", username="u", password="p")
        errors = adapter.validate_params(p)
        assert len(errors) > 0


class TestMySQLTestConnection:
    """test_connection() unit tests with mocked aiomysql."""

    @pytest.mark.asyncio
    async def test_successful_connection(self, adapter, params):
        """Returns True when aiomysql.connect() succeeds."""
        mock_conn = AsyncMock()
        mock_conn.ping = AsyncMock()

        with patch("aiomysql.connect", new=AsyncMock(return_value=mock_conn)):
            result = await adapter.test_connection(params)
            assert result is True

    @pytest.mark.asyncio
    async def test_failed_connection(self, adapter, params):
        """Returns False when aiomysql.connect() raises."""
        with patch("aiomysql.connect", side_effect=OSError("Connection refused")):
            result = await adapter.test_connection(params)
            assert result is False

    @pytest.mark.asyncio
    async def test_uses_connect_timeout(self, adapter, params):
        """Should pass connect_timeout=5 to aiomysql."""
        mock_conn = AsyncMock()
        mock_conn.ping = AsyncMock()

        with patch("aiomysql.connect", new=AsyncMock(return_value=mock_conn)) as mock_connect:
            await adapter.test_connection(params)
            call_kwargs = mock_connect.call_args.kwargs
            assert call_kwargs.get("connect_timeout") == 5


class TestMySQLScanTables:
    """scan_tables() unit tests — uses information_schema.TABLES."""

    @pytest.mark.asyncio
    async def test_returns_schema_tables(self, adapter, params):
        """Should execute information_schema query and return SchemaTable list."""
        rows = [_make_mock_row("users", "User accounts"),
                _make_mock_row("orders", "Customer orders")]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)

        with patch("app.adapters.mysql_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_tables(params)

        assert len(result) == 2
        assert isinstance(result[0], SchemaTable)
        assert result[0].table_name == "users"
        assert result[1].table_name == "orders"

    @pytest.mark.asyncio
    async def test_null_comment_handled(self, adapter, params):
        """NULL TABLE_COMMENT should result in None table_comment."""
        rows = [_make_mock_row("tbl", None)]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)

        with patch("app.adapters.mysql_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_tables(params)

        assert result[0].table_comment is None


class TestMySQLScanColumns:
    """scan_columns() unit tests — uses information_schema.COLUMNS."""

    @pytest.mark.asyncio
    async def test_returns_schema_columns(self, adapter, params):
        """Should return SchemaColumn list with correct pk detection."""
        rows = [_make_mock_row("users", "id", "INT", "NO", None, "primary key", "PRI", 1)]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)

        with patch("app.adapters.mysql_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_columns(params)

        assert len(result) == 1
        col = result[0]
        assert isinstance(col, SchemaColumn)
        assert col.table_name == "users"
        assert col.column_name == "id"
        assert col.data_type == "INT"
        assert col.nullable is False
        assert col.is_primary_key is True
        assert col.ordinal_position == 1

    @pytest.mark.asyncio
    async def test_non_pk_column(self, adapter, params):
        """COLUMN_KEY not 'PRI' → is_primary_key=False."""
        rows = [_make_mock_row("users", "email", "VARCHAR(255)", "YES", None, "email address", "", 2)]
        conn = _make_mock_conn(rows)
        engine = _make_mock_engine(conn)

        with patch("app.adapters.mysql_adapter.create_async_engine", return_value=engine):
            result = await adapter.scan_columns(params)

        assert result[0].is_primary_key is False
        assert result[0].nullable is True


class TestMySQLDialectHint:
    """get_dialect_hint() tests."""

    def test_hint_contains_mysql(self, adapter):
        hint = adapter.get_dialect_hint()
        assert "MySQL" in hint
        assert len(hint) > 0


class TestMySQLExtraFields:
    """MySQL has no extra connection fields."""

    def test_extra_fields_empty(self, adapter):
        assert adapter.get_extra_fields_schema() == {}


class TestMySQLIsSQLAlchemy:
    """MySQL uses SQLAlchemy for query execution."""

    def test_uses_sqlalchemy(self, adapter):
        assert adapter.uses_sqlalchemy() is True


class TestMySQLRegistry:
    """Verify MySQLAdapter is registered in the global registry."""

    def test_registered(self):
        import app.adapters as mod
        assert "mysql" in mod._registry

    def test_get_adapter_returns_mysql_adapter(self):
        import app.adapters as mod
        inst = mod.get_adapter("mysql")
        assert inst.db_type() == "mysql"
        assert inst.display_name() == "MySQL"
