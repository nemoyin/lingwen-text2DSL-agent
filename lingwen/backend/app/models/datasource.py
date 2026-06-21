"""DataSource connection configuration model."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

if TYPE_CHECKING:
    from app.models.table_metadata import TableMetadata
    from app.models.few_shot import FewShotExample


class DataSource(Base):
    """Data source registered in the system — supports multiple database types.

    The ``password_encrypted`` field stores an AES-256-CBC encrypted password.
    Never log or expose this field in API responses.

    The ``extra_params`` JSON column stores type-specific connection parameters
    (e.g. ``{"schema": "public"}`` for PostgreSQL, ``{"service_name": "ORCL"}``
    for Oracle).
    """

    __tablename__ = "datasources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )
    db_type: Mapped[str] = mapped_column(
        String(50), default="mysql", nullable=False
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=3306, nullable=False)
    database: Mapped[str] = mapped_column(String(200), nullable=False)
    username: Mapped[str] = mapped_column(String(200), nullable=False)
    password_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    extra_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None,
        comment="Type-specific connection parameters (schema, service_name, auth_type, etc.)",
    )
    status: Mapped[str] = mapped_column(
        String(20), default="inactive", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    tables: Mapped[List["TableMetadata"]] = relationship(
        "TableMetadata", back_populates="datasource", cascade="all, delete-orphan"
    )
    few_shot_examples: Mapped[List["FewShotExample"]] = relationship(
        "FewShotExample", back_populates="datasource", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<DataSource(id={self.id}, name={self.name!r}, "
            f"type={self.db_type!r}, status={self.status!r})>"
        )
