"""Data source Pydantic schemas."""

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


#: Supported database types (mirrors registered adapters).
DBType = Literal[
    "mysql", "postgresql", "oracle", "doris",
    "clickhouse", "hive", "elasticsearch", "csv_temp",
]


class DataSourceCreate(BaseModel):
    """Payload for creating a new data source."""

    name: str = Field(..., min_length=1, max_length=200, description="数据源名称")
    db_type: DBType = Field(default="mysql", description="数据库类型")
    host: str = Field(..., min_length=1, max_length=255, description="主机地址")
    port: int = Field(default=3306, ge=1, le=65535, description="端口号")
    database: str = Field(..., min_length=1, max_length=200, description="数据库名")
    username: str = Field(..., min_length=1, max_length=200, description="数据库用户名")
    password: str = Field(..., min_length=1, description="数据库密码（明文，存储时加密）")
    extra_params: Optional[Dict[str, Any]] = Field(
        default=None, description="类型特定的连接参数（schema, service_name, auth_type 等）"
    )


class DataSourceUpdate(BaseModel):
    """Payload for updating an existing data source.  All fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="数据源名称")
    db_type: Optional[DBType] = Field(default=None, description="数据库类型")
    host: Optional[str] = Field(default=None, min_length=1, max_length=255, description="主机地址")
    port: Optional[int] = Field(default=None, ge=1, le=65535, description="端口号")
    database: Optional[str] = Field(default=None, min_length=1, max_length=200, description="数据库名")
    username: Optional[str] = Field(default=None, min_length=1, max_length=200, description="数据库用户名")
    password: Optional[str] = Field(default=None, min_length=1, description="数据库密码（明文，存储时加密）")
    extra_params: Optional[Dict[str, Any]] = Field(
        default=None, description="类型特定的连接参数"
    )
    status: Optional[str] = Field(default=None, max_length=20, description="状态")


class DataSourceResponse(BaseModel):
    """Read-only view of a data source (password omitted)."""

    id: int
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    extra_params: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DBTypeMeta(BaseModel):
    """Metadata about one supported database type (for the front-end selector)."""

    db_type: str
    display_name: str
    default_port: int
    extra_fields: dict
