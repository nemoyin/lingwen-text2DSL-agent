"""Unit tests for DorisAdapter."""

import pytest
from app.adapters.base import ConnectionParams


@pytest.fixture
def adapter():
    from app.adapters.doris_adapter import DorisAdapter
    return DorisAdapter()


@pytest.fixture
def params():
    return ConnectionParams(host="doris-fe", port=9030, database="analytics", username="root", password="secret")


class TestDorisIdentity:
    def test_db_type(self, adapter): assert adapter.db_type() == "doris"
    def test_display_name(self, adapter): assert adapter.display_name() == "Apache Doris"
    def test_default_port(self, adapter): assert adapter.default_port() == 9030
    def test_sqlalchemy_driver(self, adapter): assert "mysql" in adapter.sqlalchemy_driver()
    def test_uses_sqlalchemy(self, adapter): assert adapter.uses_sqlalchemy() is True


class TestDorisURL:
    def test_url_contains_mysql_driver(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert url.startswith("mysql+aiomysql://")
    def test_url_contains_credentials(self, adapter, params):
        assert "root:secret" in adapter.build_connection_url(params)


class TestDorisDialectHint:
    def test_hint_mentions_doris_model(self, adapter):
        hint = adapter.get_dialect_hint()
        assert "Doris" in hint
        assert len(hint) > 10


class TestDorisExtraFields:
    def test_empty(self, adapter):
        assert adapter.get_extra_fields_schema() == {}


class TestDorisRegistry:
    def test_registered(self):
        import app.adapters as mod
        assert "doris" in mod._registry
