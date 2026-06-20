"""Skill template Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SkillCreate(BaseModel):
    """Payload for creating a new skill template."""

    name: str = Field(..., min_length=1, max_length=200, description="Skill 名称")
    description: Optional[str] = Field(default=None, description="Skill 描述")
    prompt_template: str = Field(..., min_length=1, description="Prompt 模板")
    rag_config: Optional[dict] = Field(default=None, description="RAG 配置")
    security_policy: Optional[dict] = Field(default=None, description="安全策略")
    is_active: bool = Field(default=True, description="是否激活")


class SkillUpdate(BaseModel):
    """Payload for updating an existing skill template.  All fields optional."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200, description="Skill 名称")
    description: Optional[str] = Field(default=None, description="Skill 描述")
    prompt_template: Optional[str] = Field(default=None, min_length=1, description="Prompt 模板")
    rag_config: Optional[dict] = Field(default=None, description="RAG 配置")
    security_policy: Optional[dict] = Field(default=None, description="安全策略")
    is_active: Optional[bool] = Field(default=None, description="是否激活")


class SkillResponse(BaseModel):
    """Read-only view of a skill template."""

    id: int
    name: str
    description: Optional[str] = None
    prompt_template: str
    rag_config: Optional[dict] = None
    security_policy: Optional[dict] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
