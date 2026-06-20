"""Table-level metadata for external database schemas."""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

if TYPE_CHECKING:
    from app.models.datasource import DataSource
    from app.models.column_metadata import ColumnMetadata


class TableMetadata(Base):
    """Metadata for a single table in an external data source.

    Stores the table name, a human-readable display name, and an optional
    business description used for RAG retrieval.
    """

    __tablename__ = "tables_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datasource_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False
    )
    table_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    business_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    datasource: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="tables"
    )
    columns: Mapped[List["ColumnMetadata"]] = relationship(
        "ColumnMetadata", back_populates="table", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<TableMetadata(id={self.id}, table_name={self.table_name!r}, "
            f"datasource_id={self.datasource_id})>"
        )
