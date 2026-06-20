"""Schema scan Pydantic schemas."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SchemaScanRequest(BaseModel):
    """Request to trigger a schema scan against a data source."""

    datasource_id: int = Field(..., ge=1, description="数据源 ID")


class ColumnSchema(BaseModel):
    """A single column as returned by a schema scan."""

    column_name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str] = None
    column_comment: Optional[str] = None
    is_primary_key: bool = False

    model_config = {"from_attributes": True}


class TableSchema(BaseModel):
    """A table with its columns as returned by a schema scan."""

    table_name: str
    table_comment: Optional[str] = None
    columns: List[ColumnSchema] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ScanResult(BaseModel):
    """Result of a schema scan operation."""

    datasource_id: int
    tables_scanned: int = 0
    columns_scanned: int = 0
    tables_added: int = 0
    tables_updated: int = 0
    columns_added: int = 0
    columns_updated: int = 0
    scanned_at: datetime = Field(default_factory=datetime.now)
