"""Unit tests for ElasticsearchAdapter."""

import pytest
from app.adapters.base import ConnectionParams


@pytest.fixture
def adapter():
    from app.adapters.elasticsearch_adapter import ElasticsearchAdapter
    return ElasticsearchAdapter()


@pytest.fixture
def params():
    return ConnectionParams(
        host="es.example.com", port=9200, database="my-index",
        username="elastic", password="secret",
        extra_params={"auth_type": "basic", "verify_certs": True},
    )


class TestESIdentity:
    def test_db_type(self, adapter): assert adapter.db_type() == "elasticsearch"
    def test_display_name(self, adapter): assert adapter.display_name() == "Elasticsearch"
    def test_default_port(self, adapter): assert adapter.default_port() == 9200
    def test_sqlalchemy_driver_returns_empty(self, adapter): assert adapter.sqlalchemy_driver() == ""
    def test_uses_sqlalchemy_is_false(self, adapter): assert adapter.uses_sqlalchemy() is False


class TestESURL:
    def test_builds_http_url(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert url.startswith("http://")
        assert "elastic:secret" in url
        assert "es.example.com:9200" in url

    def test_uses_https_when_secure(self, adapter):
        p = ConnectionParams(host="h", port=9200, database="idx", username="u", password="p", extra_params={"secure": True})
        url = adapter.build_connection_url(p)
        assert url.startswith("https://")


class TestESDialectHint:
    def test_hint_mentions_esql(self, adapter):
        hint = adapter.get_dialect_hint()
        assert "ES|QL" in hint
        assert len(hint) > 10


class TestESExtraFields:
    def test_includes_auth_fields(self, adapter):
        schema = adapter.get_extra_fields_schema()
        assert "auth_type" in schema
        assert "verify_certs" in schema


class TestESRegistry:
    def test_registered(self):
        import app.adapters as mod
        assert "elasticsearch" in mod._registry
