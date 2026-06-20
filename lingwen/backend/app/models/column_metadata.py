"""Column-level metadata for external database table columns."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

if TYPE_CHECKING:
    from app.models.table_metadata import TableMetadata


class ColumnMetadata(Base):
    """Metadata for a single column in a table of an external data source.

    Stores column name, type, optional display name, business description,
    enum values, and key relationship information.
    """

    __tablename__ = "columns_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tables_metadata.id", ondelete="CASCADE"), nullable=False
    )
    column_name: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    business_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enum_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_primary_key: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_foreign_key: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    foreign_ref: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    table: Mapped["TableMetadata"] = relationship(
        "TableMetadata", back_populates="columns"
    )

    def __repr__(self) -> str:
        return (
            f"<ColumnMetadata(id={self.id}, column_name={self.column_name!r}, "
            f"data_type={self.data_type!r}, table_id={self.table_id})>"
        )
