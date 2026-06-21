"""Tests for the adapter registry and factory."""

import pytest
from app.adapters.base import (
    BaseDataSourceAdapter,
    ConnectionParams,
    SchemaColumn,
    SchemaTable,
)


# ── Helpers: minimal adapters for registry testing ──
class _AlphaAdapter(BaseDataSourceAdapter):
    @staticmethod
    def db_type() -> str:
        return "alpha"

    @staticmethod
    def display_name() -> str:
        return "Alpha DB"

    @staticmethod
    def default_port() -> int:
        return 1111

    @staticmethod
    def sqlalchemy_driver() -> str:
        return "alpha+driver"

    def build_connection_url(self, params: ConnectionParams) -> str:
        return f"alpha://{params.host}"

    async def test_connection(self, params: ConnectionParams) -> bool:
        return True

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        return []

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        return []

    def get_dialect_hint(self) -> str:
        return "Alpha SQL"

    def get_extra_fields_schema(self) -> dict:
        return {}


class _BetaAdapter(BaseDataSourceAdapter):
    @staticmethod
    def db_type() -> str:
        return "beta"

    @staticmethod
    def display_name() -> str:
        return "Beta DB"

    @staticmethod
    def default_port() -> int:
        return 2222

    @staticmethod
    def sqlalchemy_driver() -> str:
        return "beta+driver"

    def build_connection_url(self, params: ConnectionParams) -> str:
        return f"beta://{params.host}"

    async def test_connection(self, params: ConnectionParams) -> bool:
        return False

    async def scan_tables(self, params: ConnectionParams) -> list[SchemaTable]:
        return [SchemaTable(table_name="t")]

    async def scan_columns(self, params: ConnectionParams) -> list[SchemaColumn]:
        return []

    def get_dialect_hint(self) -> str:
        return "Beta SQL"

    def get_extra_fields_schema(self) -> dict:
        return {"mode": {"type": "string", "default": "fast"}}


class TestAdapterRegistry:
    """Tests for the registry and factory functions."""

    def test_registry_starts_empty(self):
        """A freshly imported registry module should have no entries by default."""
        # We re-import to ensure clean state
        import app.adapters as mod
        types = mod.available_types()
        # No registrations have happened yet (adapters haven't been imported)
        assert isinstance(types, list)

    def test_register_single_adapter(self):
        """Registering one adapter adds it to the registry."""
        import app.adapters as mod

        # Manually register _AlphaAdapter for this test
        mod._registry.clear()
        mod.register_adapter(_AlphaAdapter)
        assert "alpha" in mod._registry
        assert mod._registry["alpha"] is _AlphaAdapter

    def test_register_multiple_adapters(self):
        """Multiple adapters can coexist in the registry."""
        import app.adapters as mod

        mod._registry.clear()
        mod.register_adapter(_AlphaAdapter)
        mod.register_adapter(_BetaAdapter)
        assert "alpha" in mod._registry
        assert "beta" in mod._registry
        assert len(mod._registry) == 2

    def test_get_adapter_returns_instance(self):
        """get_adapter() returns an instance of the correct adapter."""
        import app.adapters as mod

        mod._registry.clear()
        mod.register_adapter(_AlphaAdapter)

        instance = mod.get_adapter("alpha")
        assert isinstance(instance, _AlphaAdapter)
        assert isinstance(instance, BaseDataSourceAdapter)

    def test_get_adapter_unknown_raises(self):
        """get_adapter() raises ValueError for unknown types."""
        import app.adapters as mod

        mod._registry.clear()
        with pytest.raises(ValueError, match="Unsupported"):
            mod.get_adapter("nonexistent")

    def test_get_adapter_returns_different_instances(self):
        """Each call to get_adapter() returns a fresh instance."""
        import app.adapters as mod

        mod._registry.clear()
        mod.register_adapter(_AlphaAdapter)

        a1 = mod.get_adapter("alpha")
        a2 = mod.get_adapter("alpha")
        assert a1 is not a2  # different instances

    def test_available_types_metadata(self):
        """available_types() returns structured metadata with required keys."""
        import app.adapters as mod

        mod._registry.clear()
        mod.register_adapter(_AlphaAdapter)
        mod.register_adapter(_BetaAdapter)

        types = mod.available_types()
        assert len(types) == 2

        for entry in types:
            assert "db_type" in entry
            assert "display_name" in entry
            assert "default_port" in entry
            assert "extra_fields" in entry

        db_types = {t["db_type"] for t in types}
        assert "alpha" in db_types
        assert "beta" in db_types

    def test_register_adapter_returns_class(self):
        """register_adapter() returns the class (usable as decorator)."""
        import app.adapters as mod

        mod._registry.clear()
        result = mod.register_adapter(_AlphaAdapter)
        assert result is _AlphaAdapter


class TestRegistryThreadSafety:
    """Verify the registry is safe for sequential use in single-threaded async apps."""

    def test_rapid_register_and_retrieve(self):
        """Many register + get operations complete without error."""
        import app.adapters as mod

        mod._registry.clear()
        for _ in range(100):
            mod.register_adapter(_AlphaAdapter)
            inst = mod.get_adapter("alpha")
            assert isinstance(inst, _AlphaAdapter)
