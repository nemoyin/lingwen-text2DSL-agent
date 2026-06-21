"""Database adapter registry — plugin architecture for multi-DB support.

Usage
-----
    from app.adapters import get_adapter, register_adapter, available_types

    # At import time (in each adapter module):
    @register_adapter
    class MySQLAdapter(BaseDataSourceAdapter):
        ...

    # At runtime (in services):
    adapter = get_adapter("mysql")
    url = adapter.build_connection_url(params)

Adding a new adapter
--------------------
1. Create ``adapters/<name>_adapter.py``.
2. Subclass :class:`~app.adapters.base.BaseDataSourceAdapter`.
3. Decorate the class with ``@register_adapter``.
4. Import the module at the bottom of **this file** so the registry
   sees it on startup.
"""

from typing import Type, Optional

from app.adapters.base import BaseDataSourceAdapter

#: Internal mapping: db_type string → adapter class.
_registry: dict[str, Type[BaseDataSourceAdapter]] = {}


def register_adapter(
    adapter_cls: Type[BaseDataSourceAdapter],
) -> Type[BaseDataSourceAdapter]:
    """Register an adapter class in the global registry.

    Can be used as a plain function or as a class decorator::

        @register_adapter
        class MySQLAdapter(BaseDataSourceAdapter):
            ...
    """
    db_type = adapter_cls.db_type()
    _registry[db_type] = adapter_cls
    return adapter_cls


def get_adapter(db_type: str) -> BaseDataSourceAdapter:
    """Factory: return a **fresh instance** of the adapter for *db_type*.

    Args:
        db_type: e.g. ``"mysql"``, ``"postgresql"``, ``"oracle"``.

    Returns:
        A concrete :class:`BaseDataSourceAdapter` instance.

    Raises:
        ValueError: If *db_type* is not registered.
    """
    cls = _registry.get(db_type)
    if cls is None:
        raise ValueError(f"Unsupported database type: {db_type!r}")
    return cls()


def available_types() -> list[dict]:
    """Return metadata about every registered adapter.

    Used by the ``GET /api/datasources/types`` endpoint to populate the
    front-end database-type selector.

    Returns:
        A list of dicts, each containing ``db_type``, ``display_name``,
        ``default_port``, and ``extra_fields``.
    """
    return [
        {
            "db_type": cls.db_type(),
            "display_name": cls.display_name(),
            "default_port": cls.default_port(),
            "extra_fields": cls().get_extra_fields_schema(),
        }
        for cls in _registry.values()
    ]


# ── Eagerly import adapters so @register_adapter fires at startup ─────────
from app.adapters.mysql_adapter import MySQLAdapter  # noqa: E402, F401
from app.adapters.postgresql_adapter import PostgreSQLAdapter  # noqa: E402, F401
