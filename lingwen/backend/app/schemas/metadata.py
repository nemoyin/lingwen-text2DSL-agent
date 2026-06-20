"""Metadata management Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TableMetadataUpdate(BaseModel):
    """Payload for updating table-level metadata."""

    display_name: Optional[str] = Field(default=None, max_length=200, description="中文表名")
    business_description: Optional[str] = Field(default=None, description="业务描述")


class TableMetadataResponse(BaseModel):
    """Read-only view of table metadata."""

    id: int
    datasource_id: int
    table_name: str
    display_name: Optional[str] = None
    business_description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ColumnMetadataUpdate(BaseModel):
    """Payload for updating column-level metadata."""

    display_name: Optional[str] = Field(default=None, max_length=200, description="中文字段名")
    business_description: Optional[str] = Field(default=None, description="业务描述")
    enum_values: Optional[dict] = Field(default=None, description="枚举值映射")


class ColumnMetadataResponse(BaseModel):
    """Read-only view of column metadata."""

    id: int
    table_id: int
    column_name: str
    display_name: Optional[str] = None
    data_type: str
    business_description: Optional[str] = None
    enum_values: Optional[dict] = None
    is_primary_key: bool
    is_foreign_key: bool
    foreign_ref: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
