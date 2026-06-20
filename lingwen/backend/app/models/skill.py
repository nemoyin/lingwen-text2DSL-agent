"""Skill template model for configurable Agent behavior."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.database import Base


class SkillTemplate(Base):
    """Pre-configured or user-defined skill that controls Agent behavior.

    Each skill carries a prompt template, RAG configuration, and security
    policy that together define how the Agent processes user questions.
    """

    __tablename__ = "skill_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prompt_template: Mapped[str] = mapped_column(Text, nullable=False)
    rag_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    security_policy: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<SkillTemplate(id={self.id}, name={self.name!r}, "
            f"is_active={self.is_active})>"
        )
