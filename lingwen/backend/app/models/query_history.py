"""Query history model for audit logging (P2)."""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.datasource import DataSource


class QueryHistory(Base):
    """Immutable record of every natural-language-to-SQL query.

    This table serves as the audit log. It is NEVER updated after creation.
    P2 priority — skeleton only; full integration deferred.
    """

    __tablename__ = "query_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    datasource_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("datasources.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_sql: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    result_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    share_token: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    datasource: Mapped["DataSource"] = relationship("DataSource")

    def __repr__(self) -> str:
        return (
            f"<QueryHistory(id={self.id}, user_id={self.user_id}, "
            f"status={self.status!r})>"
        )
