"""Base classes and data types for the database adapter plugin architecture.

Defines the abstract base class that every database adapter must implement,
along with normalized data classes for connection parameters and schema
introspection results.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ── Normalised data types ────────────────────────────────────────────────────


@dataclass
class ConnectionParams:
    """Normalised connection parameters passed to every adapter.

    Each adapter's concrete methods receive a ``ConnectionParams`` instance
    with all fields populated from the ``datasources`` table row.  The
    ``extra_params`` dict holds type-specific settings (e.g. Oracle
    ``service_name``, PostgreSQL ``schema``, Elasticsearch ``auth_type``).
    """

    host: str
    port: int
    database: str          # database name, schema, or ES index
    username: str
    password: str          # plaintext (already decrypted by the caller)
    extra_params: dict = field(default_factory=dict)


@dataclass
class SchemaTable:
    """One user table / collection discovered during schema introspection."""

    table_name: str
    table_comment: Optional[str] = None
    row_count_estimate: Optional[int] = None


@dataclass
class SchemaColumn:
    """One column / field discovered during schema introspection.

    All adapter ``scan_columns()`` implementations must return a flat list
    of ``SchemaColumn`` objects.  The ``table_name`` field on each column
    links it back to its parent table.
    """

    table_name: str
    column_name: str
    data_type: str
    nullable: bool = True
    default_value: Optional[str] = None
    comment: Optional[str] = None
    is_primary_key: bool = False
    ordinal_position: int = 0


# ── Abstract base adapter ────────────────────────────────────────────────────


class BaseDataSourceAdapter(ABC):
    """Abstract base for all database adapters.

    Every concrete adapter handles **one** database type and must implement
    every abstract method declared below.  The registry in ``adapters/__init__.py``
    discovers adapters and maps ``db_type()`` → adapter class.

    Lifecycle
    ---------
    1. ``get_adapter("mysql")`` returns a fresh *or* cached adapter instance.
    2. The caller builds ``ConnectionParams`` from the ``datasources`` row.
    3. ``adapter.test_connection(params)`` or ``adapter.scan_tables(params)``
       is called with those params.

    Adding a new database type
    --------------------------
    1. Create ``adapters/<name>_adapter.py``.
    2. Subclass ``BaseDataSourceAdapter`` and implement every abstract method.
    3. Decorate the class with ``@register_adapter`` (from ``adapters/__init__``).
    4. Import the module in ``adapters/__init__.py`` so the registry sees it.
    """

    # ── Static identity ──────────────────────────────────────────────────

    @staticmethod
    @abstractmethod
    def db_type() -> str:
        """Return the ``db_type`` identifier, e.g. ``"mysql"``, ``"postgresql"``.

        This value is stored in the ``datasources.db_type`` column and used
        as the registry key.  It must be unique across all adapters.
        """
        ...

    @staticmethod
    @abstractmethod
    def display_name() -> str:
        """Human-readable label shown in the UI, e.g. ``"MySQL"``, ``"PostgreSQL"``."""
        ...

    @staticmethod
    @abstractmethod
    def default_port() -> int:
        """Default TCP port for this database type, e.g. 3306 for MySQL."""
        ...

    @staticmethod
    @abstractmethod
    def sqlalchemy_driver() -> str:
        """SQLAlchemy async driver prefix, e.g. ``"mysql+aiomysql"``.

        Return an empty string for adapters that do not use SQLAlchemy
        (e.g. Elasticsearch).
        """
        ...

    # ── Connection ───────────────────────────────────────────────────────

    @abstractmethod
    def build_connection_url(self, params: ConnectionParams) -> str:
        """Build a database connection URL string from *params*.

        For SQLAlchemy-based adapters this is the URL passed to
        :func:`sqlalchemy.ext.asyncio.create_async_engine`.  For non-SQL
        adapters (Elasticsearch) it can be a canonical string used as a
        cache key.
        """
        ...

    @abstractmethod
    async def test_connection(self, params: ConnectionParams) -> bool:
        """Open a short-lived connection and verify it works.

        Returns:
            ``True`` if the connection succeeded, ``False`` otherwise.
        """
        ...

    # ── Schema introspection ─────────────────────────────────────────────

    @abstractmethod
    async def scan_tables(
        self, params: ConnectionParams
    ) -> list[SchemaTable]:
        """Return metadata about every user table / collection.

        The returned list is used to populate ``tables_metadata`` rows.
        """
        ...

    @abstractmethod
    async def scan_columns(
        self, params: ConnectionParams
    ) -> list[SchemaColumn]:
        """Return metadata about every column / field across all user tables.

        Each returned ``SchemaColumn`` must have its ``table_name`` set so
        the caller can group columns by table.
        """
        ...

    # ── Query generation hints ───────────────────────────────────────────

    @abstractmethod
    def get_dialect_hint(self) -> str:
        """Return a short dialect description for the SQL-generation prompt.

        Example for MySQL:
            ``"MySQL SQL 查询。注意使用反引号标识符，LIMIT 分页。"``

        Example for PostgreSQL:
            ``"PostgreSQL SQL 查询。注意使用双引号标识符，::类型转换。"``
        """
        ...

    # ── Frontend form schema ─────────────────────────────────────────────

    @abstractmethod
    def get_extra_fields_schema(self) -> dict:
        """Return a JSON-Schema-like dict describing type-specific form fields.

        Used by the front-end to dynamically render extra connection fields
        when the user selects this database type.  Return an empty dict if
        no extra fields are needed.

        Example for PostgreSQL::

            {"schema": {"type": "string", "default": "public"}}

        Example for Oracle::

            {"service_name": {"type": "string"},
             "sid":          {"type": "string"}}
        """
        ...

    # ── Validation ───────────────────────────────────────────────────────

    def validate_params(self, params: ConnectionParams) -> list[str]:
        """Validate *params* and return a list of human-readable error messages.

        The base implementation checks that host, port, and username are
        non-empty.  Subclasses should override to add type-specific checks
        (e.g. Oracle requires ``service_name`` **or** ``sid`` in extra_params).

        Returns:
            An empty list when all checks pass.
        """
        errors: list[str] = []
        if not params.host:
            errors.append("主机地址不能为空")
        if not params.port or params.port <= 0:
            errors.append("端口号无效")
        if not params.username:
            errors.append("用户名不能为空")
        return errors

    # ── Query execution (non-SQL adapters) ──────────────────────────────

    async def execute_query(
        self, params: ConnectionParams, query: str
    ) -> list[dict]:
        """Execute a read-only query and return rows as dicts.

        The default implementation raises ``NotImplementedError``.
        Non-SQLAlchemy adapters (e.g. Elasticsearch) **must** override this
        method.  SQLAlchemy-based adapters are handled by the service layer
        and do not need to implement it.

        Args:
            params: Decrypted connection parameters.
            query: The validated query string (SQL, ES|QL, etc.).

        Returns:
            A list of dicts, each representing one row.
        """
        raise NotImplementedError(
            f"{self.db_type()} adapter does not implement execute_query()"
        )

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def dispose(self) -> None:
        """Release any adapter-level resources (connection pools, etc.).

        Called when a data source is deleted or its configuration changes.
        The default implementation is a no-op.
        """
        pass
