"""Few-shot example Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FewShotCreate(BaseModel):
    """Payload for creating a new few-shot example."""

    datasource_id: int = Field(..., ge=1, description="关联数据源 ID")
    question: str = Field(..., min_length=1, description="自然语言问题")
    sql: str = Field(..., min_length=1, description="对应的正确 SQL")
    description: Optional[str] = Field(default=None, description="示例说明")
    tags: Optional[str] = Field(default=None, max_length=500, description="标签（逗号分隔）")


class FewShotUpdate(BaseModel):
    """Payload for updating an existing few-shot example.  All fields optional."""

    question: Optional[str] = Field(default=None, min_length=1, description="自然语言问题")
    sql: Optional[str] = Field(default=None, min_length=1, description="对应的正确 SQL")
    description: Optional[str] = Field(default=None, description="示例说明")
    tags: Optional[str] = Field(default=None, max_length=500, description="标签")


class FewShotResponse(BaseModel):
    """Read-only view of a few-shot example."""

    id: int
    datasource_id: int
    question: str
    sql: str
    description: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
