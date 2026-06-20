"""Few-shot example model for Text-to-SQL training."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

if TYPE_CHECKING:
    from app.models.datasource import DataSource


class FewShotExample(Base):
    """A question→SQL pair used as a RAG retrieval example.

    Each example is associated with a data source. The ``tags`` field can
    contain comma-separated keywords for keyword-based filtering.
    """

    __tablename__ = "few_shot_examples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    datasource_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    sql: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    datasource: Mapped["DataSource"] = relationship(
        "DataSource", back_populates="few_shot_examples"
    )

    def __repr__(self) -> str:
        return (
            f"<FewShotExample(id={self.id}, question={self.question[:50]!r}..., "
            f"datasource_id={self.datasource_id})>"
        )
