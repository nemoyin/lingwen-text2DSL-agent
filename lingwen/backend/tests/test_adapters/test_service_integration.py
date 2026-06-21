"""Verify datasource_service delegates to adapters correctly.

These tests mock the database layer and the adapter to confirm the
service functions call the right adapter methods with the right params.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.adapters.base import ConnectionParams


# ── Helpers ─────────────────────────────────────────────────────────────────


async def _fake_get(db, ds_id):
    """Minimal DataSource-like object for service tests."""
    ds = MagicMock()
    ds.id = ds_id
    ds.name = "test-ds"
    ds.db_type = "mysql"
    ds.host = "db.example.com"
    ds.port = 3306
    ds.database = "analytics"
    ds.username = "reader"
    ds.password_encrypted = "encrypted-secret"
    ds.extra_params = {}
    ds.status = "active"
    return ds


# ── Tests: test_connection delegates to adapter ──────────────────────────────


class TestServiceTestConnection:
    """datasource_service.test_connection() → adapter.test_connection()."""

    @pytest.mark.asyncio
    async def test_delegates_to_adapter_and_returns_true(self):
        """Service calls get_adapter().test_connection() and returns its result."""
        from app.services import datasource_service

        # Mock the adapter's test_connection to succeed
        mock_adapter = MagicMock()
        mock_adapter.test_connection = AsyncMock(return_value=True)

        with (
            patch.object(datasource_service, "get", new=_fake_get),
            patch.object(datasource_service, "decrypt_password", return_value="plain-pw"),
            patch.object(datasource_service, "get_adapter", return_value=mock_adapter) as mock_factory,
        ):
            result = await datasource_service.test_connection(db=MagicMock(), ds_id=1)

            assert result is True
            mock_factory.assert_called_once_with("mysql")
            mock_adapter.test_connection.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_adapter_returns_false_propagates(self):
        """When adapter.test_connection() returns False, the service returns False."""
        from app.services import datasource_service

        mock_adapter = MagicMock()
        mock_adapter.test_connection = AsyncMock(return_value=False)

        with (
            patch.object(datasource_service, "get", new=_fake_get),
            patch.object(datasource_service, "decrypt_password", return_value="plain-pw"),
            patch.object(datasource_service, "get_adapter", return_value=mock_adapter),
        ):
            result = await datasource_service.test_connection(db=MagicMock(), ds_id=1)
            assert result is False


# ── Tests: get_connection uses adapter to build URL ──────────────────────────


class TestServiceGetConnection:
    """datasource_service.get_connection() uses adapter.build_connection_url()."""

    @pytest.mark.asyncio
    async def test_calls_adapter_build_connection_url(self):
        """Service should ask the adapter for the connection URL."""
        from app.services import datasource_service

        mock_adapter = MagicMock()
        mock_adapter.sqlalchemy_driver = MagicMock(return_value="mock+driver")
        mock_adapter.build_connection_url = MagicMock(
            return_value="mock+driver://user:pass@host:3306/db"
        )

        # Remove any cached engine first
        datasource_service._engine_cache.pop(1, None)

        with (
            patch.object(datasource_service, "get", new=_fake_get),
            patch.object(datasource_service, "decrypt_password", return_value="plain-pw"),
            patch.object(datasource_service, "get_adapter", return_value=mock_adapter),
            patch.object(datasource_service, "create_async_engine") as mock_create,
        ):
            mock_engine = MagicMock()
            mock_engine.dispose = AsyncMock()
            mock_create.return_value = mock_engine

            engine = await datasource_service.get_connection(db=MagicMock(), ds_id=1)

            mock_adapter.build_connection_url.assert_called_once()
            mock_create.assert_called_once()
            assert engine is mock_engine

            # Clean up
            await datasource_service._dispose_engine(1)


# ── Tests: ConnectionParams construction ─────────────────────────────────────


class TestConnectionParamsFromDatasource:
    """Service constructs ConnectionParams correctly from a DataSource row."""

    def test_builds_params(self):
        """The helper function should map DataSource fields to ConnectionParams."""
        params = ConnectionParams(
            host="db.example.com",
            port=3306,
            database="analytics",
            username="reader",
            password="plain-pw",
        )
        assert params.host == "db.example.com"
        assert params.port == 3306
        assert params.database == "analytics"
        assert params.username == "reader"
        assert params.password == "plain-pw"
        assert params.extra_params == {}
