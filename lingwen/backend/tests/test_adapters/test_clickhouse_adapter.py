"""Unit tests for ClickHouseAdapter."""

import pytest
from app.adapters.base import ConnectionParams


@pytest.fixture
def adapter():
    from app.adapters.clickhouse_adapter import ClickHouseAdapter
    return ClickHouseAdapter()


@pytest.fixture
def params():
    return ConnectionParams(host="ch.example.com", port=8123, database="default", username="default", password="secret")


class TestClickHouseIdentity:
    def test_db_type(self, adapter): assert adapter.db_type() == "clickhouse"
    def test_display_name(self, adapter): assert adapter.display_name() == "ClickHouse"
    def test_default_port(self, adapter): assert adapter.default_port() == 8123
    def test_sqlalchemy_driver(self, adapter): assert "clickhouse" in adapter.sqlalchemy_driver()
    def test_uses_sqlalchemy(self, adapter): assert adapter.uses_sqlalchemy() is True


class TestClickHouseURL:
    def test_url_contains_driver(self, adapter, params):
        assert "clickhouse" in adapter.build_connection_url(params)
    def test_url_contains_host(self, adapter, params):
        assert params.host in adapter.build_connection_url(params)


class TestClickHouseDialectHint:
    def test_hint_mentions_clickhouse(self, adapter):
        hint = adapter.get_dialect_hint()
        assert "ClickHouse" in hint
        assert len(hint) > 20


class TestClickHouseExtraFields:
    def test_includes_secure_toggle(self, adapter):
        schema = adapter.get_extra_fields_schema()
        assert "secure" in schema


class TestClickHouseRegistry:
    def test_registered(self):
        import app.adapters as mod
        assert "clickhouse" in mod._registry
