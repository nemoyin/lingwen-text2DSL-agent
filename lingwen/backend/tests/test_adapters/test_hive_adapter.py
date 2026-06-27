"""Unit tests for HiveAdapter."""

import pytest
from app.adapters.base import ConnectionParams


@pytest.fixture
def adapter():
    from app.adapters.hive_adapter import HiveAdapter
    return HiveAdapter()


@pytest.fixture
def params():
    return ConnectionParams(host="hive-server", port=10000, database="default", username="hive", password="secret")


class TestHiveIdentity:
    def test_db_type(self, adapter): assert adapter.db_type() == "hive"
    def test_display_name(self, adapter): assert adapter.display_name() == "Apache Hive"
    def test_default_port(self, adapter): assert adapter.default_port() == 10000
    def test_sqlalchemy_driver(self, adapter): assert "hive" in adapter.sqlalchemy_driver()
    def test_uses_sqlalchemy(self, adapter): assert adapter.uses_sqlalchemy() is False


class TestHiveURL:
    def test_url_contains_hive_driver(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "hive" in url
    def test_url_contains_credentials(self, adapter, params):
        assert "hive:secret" in adapter.build_connection_url(params)


class TestHiveDialectHint:
    def test_hint_mentions_hiveql(self, adapter):
        hint = adapter.get_dialect_hint()
        assert "HiveQL" in hint
        assert len(hint) > 20


class TestHiveExtraFields:
    def test_empty(self, adapter):
        assert adapter.get_extra_fields_schema() == {}


class TestHiveRegistry:
    def test_registered(self):
        import app.adapters as mod
        assert "hive" in mod._registry
