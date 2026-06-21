"""Unit tests for OracleAdapter."""

import pytest
from app.adapters.base import ConnectionParams


@pytest.fixture
def adapter():
    from app.adapters.oracle_adapter import OracleAdapter
    return OracleAdapter()


@pytest.fixture
def params():
    return ConnectionParams(
        host="ora.example.com", port=1521, database="ORCLPDB1",
        username="scott", password="tiger",
        extra_params={"service_name": "ORCL"},
    )


class TestOracleIdentity:
    def test_db_type(self, adapter): assert adapter.db_type() == "oracle"
    def test_display_name(self, adapter): assert adapter.display_name() == "Oracle"
    def test_default_port(self, adapter): assert adapter.default_port() == 1521
    def test_sqlalchemy_driver(self, adapter): assert "oracle" in adapter.sqlalchemy_driver()
    def test_uses_sqlalchemy(self, adapter): assert adapter.uses_sqlalchemy() is True


class TestOracleURL:
    def test_url_contains_oracle_driver(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert url.startswith("oracle+oracledb://")
    def test_url_contains_service_name(self, adapter, params):
        url = adapter.build_connection_url(params)
        assert "service_name=ORCL" in url
    def test_url_uses_sid_when_no_service_name(self, adapter):
        p = ConnectionParams(host="h", port=1521, database="db", username="u", password="p", extra_params={"sid": "ORCLSID"})
        url = adapter.build_connection_url(p)
        assert "sid=ORCLSID" in url


class TestOracleValidateParams:
    def test_missing_service_and_sid(self, adapter):
        p = ConnectionParams(host="h", port=1521, database="db", username="u", password="p")
        errors = adapter.validate_params(p)
        assert len(errors) > 0
        assert any("service_name" in e or "sid" in e for e in errors)


class TestOracleDialectHint:
    def test_hint_mentions_oracle(self, adapter):
        hint = adapter.get_dialect_hint()
        assert "Oracle" in hint
        assert len(hint) > 20


class TestOracleExtraFields:
    def test_includes_service_name_and_sid(self, adapter):
        schema = adapter.get_extra_fields_schema()
        assert "service_name" in schema
        assert "sid" in schema


class TestOracleRegistry:
    def test_registered(self):
        import app.adapters as mod
        assert "oracle" in mod._registry
